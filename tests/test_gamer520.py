# ruff: noqa: S101
"""Gamer520 解析测试，包括按真实页面结构缩减的免费入口样本。"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from nonebot.exception import FinishedException

from nonebot_plugin_game_torrent import __main__ as plugin
from nonebot_plugin_game_torrent import source
from nonebot_plugin_game_torrent.exception import RequestError
from nonebot_plugin_game_torrent.fetcher import AHF, FGF, G520F, ZYKF, TorrentTag
from nonebot_plugin_game_torrent.source import SourceManager

FREE_ENTRY_HTML = (
    Path(__file__).parent / "fixtures" / "gamer520_free_entry.html"
).read_text(encoding="utf-8")


@pytest_asyncio.fixture
async def make_fetcher():
    clients = []

    def factory(handler):
        fetcher = G520F()
        fetcher._client = httpx.AsyncClient(
            base_url=fetcher.base_url,
            transport=httpx.MockTransport(handler),
            follow_redirects=True,
        )
        clients.append(fetcher._client)
        return fetcher

    yield factory
    for client in clients:
        await client.aclose()


@pytest.mark.parametrize("title_class", ["entry-title", "post-title"])
async def test_search_encodes_keyword_and_filters_links(make_fetcher, title_class):
    def handler(request):
        assert request.url.params["s"] == "游戏 & Game"
        return httpx.Response(
            200,
            text=f"""
            <h2 class="{title_class}"><a href="/123.html">游戏 <b>Game</b></a></h2>
            <h2 class="{title_class}"><a href="/123.html#download">重复</a></h2>
            <h2 class="{title_class}"><a href="https://ads.example/">广告</a></h2>
            <h2 class="{title_class}"><a href="/category/games/">分类</a></h2>
            <h2 class="{title_class}"><a href="/">首页</a></h2>
            <h2 class="{title_class}"><a href="/empty.html"> </a></h2>
            <a href="/unrelated.html">站点导航</a>
            """,
        )

    assert await make_fetcher(handler).search("游戏 & Game") == [
        TorrentTag(game_name="游戏 Game", url="https://www.gamer520.com/123.html")
    ]


async def test_blank_search_does_not_request(make_fetcher):
    handler = AsyncMock()
    assert await make_fetcher(handler).search("  ") == []
    handler.assert_not_called()


async def test_empty_search(make_fetcher):
    fetcher = make_fetcher(lambda _: httpx.Response(200, text="<p>未找到</p>"))
    assert await fetcher.search("missing") == []


@pytest.mark.parametrize(
    "content_class", ["entry-content", "wp-posts-content", "article-content"]
)
async def test_fetch_prefers_magnet_and_extracts_metadata(make_fetcher, content_class):
    html = f"""
    <meta property="article:published_time" content="2026-01-01">
    <meta property="article:modified_time" content="2026-10-21">
    <div class="{content_class}">
      <p>游戏大小：1.5 GiB</p>
      <a href="https://pan.baidu.com/s/example?pwd=abcd">网盘</a>
      <a href="magnet:?xt=urn:btih:example&amp;dn=game">磁力</a>
    </div>
    """
    resource = await make_fetcher(lambda _: httpx.Response(200, text=html)).fetch(
        TorrentTag(game_name="Game", url="/123.html")
    )
    assert resource is not None
    assert resource.game_name == "Game"
    assert resource.magnet == "magnet:?xt=urn:btih:example&dn=game"
    assert resource.size == "1.5 GiB"
    assert resource.last_update == "2026-10-21"


@pytest.mark.parametrize(
    "link",
    [
        '<a href="//pan.quark.cn/s/example?pwd=abcd">下载</a>',
        "https://pan.quark.cn/s/example?pwd=abcd",
    ],
)
async def test_fetch_share_link_and_unknown_metadata(make_fetcher, link):
    html = f'<div class="entry-content">{link}</div>'
    resource = await make_fetcher(lambda _: httpx.Response(200, text=html)).fetch(
        TorrentTag(game_name="Game", url="/123.html")
    )
    assert resource is not None
    assert resource.magnet == "https://pan.quark.cn/s/example?pwd=abcd"
    assert resource.size == "Unknown"
    assert resource.last_update == "Unknown"


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        ('<meta property="article:published_time" content="2026-01-01">', "2026-01-01"),
        (
            '<div class="entry-meta"><time datetime="2026-02-02">今天</time></div>',
            "2026-02-02",
        ),
    ],
)
async def test_date_fallback(make_fetcher, metadata, expected):
    html = metadata + '<div class="entry-content">magnet:?xt=urn:btih:example</div>'
    resource = await make_fetcher(lambda _: httpx.Response(200, text=html)).fetch(
        TorrentTag(game_name="Game", url="/123.html")
    )
    assert resource is not None
    assert resource.last_update == expected


@pytest.mark.parametrize(
    "html",
    [
        '<a href="magnet:?xt=outside">推荐内容</a>',
        '<div class="entry-content">需要登录后下载</div>',
        '<div class="entry-content"><a href="/go?key=encrypted">下载</a></div>',
        '<div class="entry-content"><a href="https://ads.example/">广告</a></div>',
        '<div class="entry-content"><a href="https://pan.baidu.com.evil.example/s/x">广告</a></div>',
    ],
)
async def test_missing_public_resource_returns_none(make_fetcher, html):
    fetcher = make_fetcher(lambda _: httpx.Response(200, text=html))
    assert await fetcher.fetch(TorrentTag(game_name="Game", url="/123.html")) is None


@pytest.mark.parametrize("operation", ["search", "fetch"])
@pytest.mark.parametrize("failure", [403, 500, "timeout"])
async def test_http_errors_are_wrapped(make_fetcher, operation, failure):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(failure)

    argument = (
        "Game" if operation == "search" else TorrentTag(game_name="Game", url="/1")
    )
    with pytest.raises(RequestError, match=f"gamer520 {operation} error"):
        await getattr(make_fetcher(handler), operation)(argument)


async def test_external_detail_url_is_rejected_without_request(make_fetcher):
    handler = AsyncMock()
    with pytest.raises(RequestError, match="outside"):
        await make_fetcher(handler).fetch(
            TorrentTag(game_name="Game", url="https://ads.example/123.html")
        )
    handler.assert_not_called()


async def test_search_follows_same_site_redirect(make_fetcher):
    def handler(request):
        if request.url.path == "/":
            return httpx.Response(302, headers={"Location": "/results"})
        return httpx.Response(
            200, text='<h2 class="entry-title"><a href="/1">Game</a></h2>'
        )

    assert len(await make_fetcher(handler).search("Game")) == 1


async def test_real_page_structure_returns_free_entry_without_following(make_fetcher):
    requests = []

    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, text=FREE_ENTRY_HTML)

    resource = await make_fetcher(handler).fetch(
        TorrentTag(game_name="Example Game", url="/123.html")
    )
    assert resource is not None
    assert resource.magnet == "https://www.gamer520.com/go?post_id=123"
    assert resource.last_update == "2026-08-21T07:57:41+08:00"
    assert resource.size == "Unknown"
    assert requests == ["https://www.gamer520.com/123.html"]


@pytest.mark.parametrize("price", ["¥10", "会员免费", "登录后免费", ""])
async def test_paid_or_conditional_entry_is_not_returned(make_fetcher, price):
    html = FREE_ENTRY_HTML.replace('class="price">免费', f'class="price">{price}')
    fetcher = make_fetcher(lambda _: httpx.Response(200, text=html))
    assert await fetcher.fetch(TorrentTag(game_name="Game", url="/123.html")) is None


@pytest.mark.parametrize(
    "entry",
    [
        "https://ads.example/go?post_id=123",
        "https://www.gamer520.com/go?post_id=456",
        "https://www.gamer520.com/go?post_id=123&key=encrypted",
        "https://www.gamer520.com/go?post_id=123&post_id=456",
        "https://www.gamer520.com/other?post_id=123",
    ],
)
async def test_entry_must_be_the_current_posts_official_link(make_fetcher, entry):
    html = FREE_ENTRY_HTML.replace("https://www.gamer520.com/go?post_id=123", entry)
    fetcher = make_fetcher(lambda _: httpx.Response(200, text=html))
    assert await fetcher.fetch(TorrentTag(game_name="Game", url="/123.html")) is None


async def test_public_magnet_takes_priority_over_sidebar(make_fetcher):
    html = FREE_ENTRY_HTML.replace("游戏介绍", '<a href="magnet:?xt=example">磁力</a>')
    resource = await make_fetcher(lambda _: httpx.Response(200, text=html)).fetch(
        TorrentTag(game_name="Game", url="/123.html")
    )
    assert resource is not None
    assert resource.magnet == "magnet:?xt=example"


async def test_source_command_selects_fourth_source(tmp_path):
    manager = SourceManager((AHF(), FGF(), ZYKF(), G520F()), tmp_path / "source.text")
    matcher = SimpleNamespace(finish=AsyncMock(side_effect=FinishedException))
    with pytest.raises(FinishedException):
        await plugin.change_source(
            matcher, SimpleNamespace(available=True, result="4"), manager
        )
    assert isinstance(manager.current, G520F)
    matcher.finish.assert_awaited_once_with("已更换至Gamer520")


def test_default_provider_appends_gamer520_without_reordering(tmp_path, monkeypatch):
    monkeypatch.setattr(
        source.store.plugin_config,
        "localstore_plugin_config_dir",
        {"nonebot_plugin_game_torrent": tmp_path},
    )
    source.get_source_manager.cache_clear()
    try:
        manager = source.get_source_manager()
        assert [type(fetcher) for fetcher in manager.fetchers] == [
            AHF,
            FGF,
            ZYKF,
            G520F,
        ]
    finally:
        source.get_source_manager.cache_clear()
