# ruff: noqa: S101

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from nonebot.exception import FinishedException

from nonebot_plugin_game_torrent import __main__ as plugin
from nonebot_plugin_game_torrent.exception import RequestError
from nonebot_plugin_game_torrent.fetcher import ZYKF, TorrentTag
from nonebot_plugin_game_torrent.source import SourceManager

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def make_fetcher():
    clients = []

    def factory(handler):
        fetcher = ZYKF()
        fetcher._client = httpx.AsyncClient(
            base_url=fetcher.base_url, transport=httpx.MockTransport(handler)
        )
        clients.append(fetcher._client)
        return fetcher

    yield factory
    for client in clients:
        await client.aclose()


async def test_search_encodes_keywords_and_filters_results(make_fetcher):
    def handler(request):
        assert request.url.params["s"] == "奥日 & Ori"
        assert request.url.params["type"] == "post"
        return httpx.Response(
            200,
            text="""
            <h2 class="item-heading"><a href="/4947">奥日 <b>Ori</b></a></h2>
            <h2 class="item-heading"><a href="/4947">重复</a></h2>
            <h2 class="item-heading"><a>缺少链接</a></h2>
            <h2 class="item-heading"><a href="/empty"> </a></h2>
            <h2 class="item-heading"><a href="https://ads.example/">广告</a></h2>
            <h2 class="item-heading"><a href="javascript:void(0)">无效</a></h2>
            <a href="/other">导航</a>
            """,
        )

    tags = await make_fetcher(handler).search("奥日 & Ori")
    assert tags == [TorrentTag(game_name="奥日 Ori", url="https://www.123zyk.com/4947")]


async def test_empty_search_results(make_fetcher):
    fetcher = make_fetcher(lambda _: httpx.Response(200, text="<p>没有找到内容</p>"))
    assert await fetcher.search("missing") == []


async def test_blank_keyword_does_not_request(make_fetcher):
    handler = AsyncMock()
    assert await make_fetcher(handler).search("  ") == []
    handler.assert_not_called()


async def test_fetch_share_link_and_size(make_fetcher):
    html = """
    <div class="article-content"><div class="wp-posts-content">
      <h4>版本介绍</h4><p>v1.0|容量11GB|官方简体中文</p>
      <h2>游戏下载</h2>
      <p>夸克：<a href="https://pan.123zyk.com/s/example">下载</a></p>
      <a href="https://www.123zyk.com/8957">帮助中心</a>
      <a href="https://ads.example/">赞助商</a>
    </div></div>
    <aside><time datetime="2025-01-01">相关推荐时间</time></aside>
    """
    fetcher = make_fetcher(lambda _: httpx.Response(200, text=html))
    resource = await fetcher.fetch(TorrentTag(game_name="奥日", url="/4947"))
    assert resource is not None
    assert resource.game_name == "奥日"
    assert resource.magnet == "https://pan.123zyk.com/s/example"
    assert resource.size == "11GB"
    assert resource.last_update == "Unknown"
    assert resource.magnet in str(resource)


async def test_magnet_takes_priority_and_modified_date_wins(make_fetcher):
    html = """
    <meta property="article:published_time" content="2025-01-01">
    <meta property="article:modified_time" content="2026-10-10">
    <div class="wp-posts-content">
      <p>游戏大小： 1.5 GiB</p>
      <a href="//pan.quark.cn/s/example">网盘</a>
      <a href="magnet:?xt=urn:btih:example&amp;dn=game">磁力</a>
    </div>
    """
    fetcher = make_fetcher(lambda _: httpx.Response(200, text=html))
    resource = await fetcher.fetch(TorrentTag(game_name="Game", url="/1"))
    assert resource is not None
    assert resource.magnet == "magnet:?xt=urn:btih:example&dn=game"
    assert resource.size == "1.5 GiB"
    assert resource.last_update == "2026-10-10"


@pytest.mark.parametrize(
    ("date_html", "expected"),
    [
        ('<meta property="article:published_time" content="2026-01-01">', "2026-01-01"),
        (
            '<div class="article-header"><time datetime="2026-02-02">今天</time></div>',
            "2026-02-02",
        ),
        ("", "Unknown"),
    ],
)
async def test_metadata_fallbacks(make_fetcher, date_html, expected):
    html = (
        date_html
        + """
    <div class="wp-posts-content"><a href="//pan.quark.cn/s/example">下载</a></div>
    """
    )
    resource = await make_fetcher(lambda _: httpx.Response(200, text=html)).fetch(
        TorrentTag(game_name="Game", url="/1")
    )
    assert resource is not None
    assert resource.magnet == "https://pan.quark.cn/s/example"
    assert resource.size == "Unknown"
    assert resource.last_update == expected


@pytest.mark.parametrize(
    "html",
    [
        "<p>缺少正文</p>",
        '<div class="wp-posts-content"><p>敬请期待</p></div>',
        '<div class="wp-posts-content"><a href="https://ads.example/">广告</a></div>',
        '<div class="wp-posts-content"></div><a href="magnet:?xt=other">推荐内容</a>',
    ],
)
async def test_missing_download_returns_none(make_fetcher, html):
    fetcher = make_fetcher(lambda _: httpx.Response(200, text=html))
    assert await fetcher.fetch(TorrentTag(game_name="Game", url="/1")) is None


@pytest.mark.parametrize("operation", ["search", "fetch"])
@pytest.mark.parametrize("failure", [403, 404, 500, "timeout"])
async def test_request_failures_are_wrapped(make_fetcher, operation, failure):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(failure)

    fetcher = make_fetcher(handler)
    argument = (
        "Game" if operation == "search" else TorrentTag(game_name="Game", url="/1")
    )
    with pytest.raises(RequestError, match=f"123zyk {operation} error"):
        await getattr(fetcher, operation)(argument)


async def test_search_follows_redirect(make_fetcher):
    def handler(request):
        if request.url.path == "/":
            return httpx.Response(302, headers={"Location": "/results"})
        return httpx.Response(
            200, text='<h2 class="item-heading"><a href="/1">Game</a></h2>'
        )

    assert len(await make_fetcher(handler).search("Game")) == 1


async def test_source_command_switches_to_zyk123(tmp_path):
    manager = SourceManager((ZYKF(), ZYKF(), ZYKF()), tmp_path / "source.text")
    matcher = SimpleNamespace(finish=AsyncMock(side_effect=FinishedException))
    with pytest.raises(FinishedException):
        await plugin.change_source(
            matcher, SimpleNamespace(available=True, result="3"), manager
        )
    assert manager.current is manager.fetchers[-1]
    assert isinstance(manager.current, ZYKF)
    matcher.finish.assert_awaited_once_with("已更换至123资源库")
