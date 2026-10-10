# ruff: noqa: S101

import asyncio
import io
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from nonebot.exception import FinishedException
from PIL import Image

from nonebot_plugin_game_torrent import __main__ as plugin
from nonebot_plugin_game_torrent import hook
from nonebot_plugin_game_torrent.exception import RequestError
from nonebot_plugin_game_torrent.fetcher import AHF, FGF, TorrentTag
from nonebot_plugin_game_torrent.source import SourceManager
from nonebot_plugin_game_torrent.utils import url2qrcode_bytes


def test_qrcode_is_valid_png():
    data = url2qrcode_bytes("https://example.com/resource")
    with Image.open(io.BytesIO(data)) as image:
        assert image.format == "PNG"
        image.verify()


@pytest.mark.parametrize("saved", [None, "", "invalid", "-1", "999", "2"])
async def test_startup_and_shutdown_persist_source(tmp_path, monkeypatch, saved):
    path = tmp_path / "config" / "game_torrent.text"
    if saved is not None:
        path.parent.mkdir()
        path.write_text(saved, encoding="utf-8")
    manager = SourceManager((AHF(), FGF(), AHF()), path)
    monkeypatch.setattr(hook, "get_source_manager", lambda: manager)
    await hook.check_source()
    assert manager.current_index == (2 if saved == "2" else 0)
    client = manager.fetchers[0].client
    manager.select(1)
    await hook.save_source()
    assert await asyncio.to_thread(path.read_text, encoding="utf-8") == "1"
    assert client.is_closed


async def test_shutdown_closes_clients_when_config_write_fails(monkeypatch, tmp_path):
    manager = SourceManager((AHF(),), tmp_path / "source.text")
    monkeypatch.setattr(hook, "get_source_manager", lambda: manager)

    def fail_write(_index):
        raise PermissionError("read-only config")

    monkeypatch.setattr(manager, "_write_index", fail_write)
    client = manager.current.client
    await hook.save_source()
    assert client.is_closed


@pytest.mark.parametrize("value", ["0", "4", "-1", "²", "abc"])
async def test_invalid_source_selection(tmp_path, value):
    manager = SourceManager((AHF(), FGF()), tmp_path / "source.text")
    matcher = SimpleNamespace(finish=AsyncMock(side_effect=FinishedException))
    with pytest.raises(FinishedException):
        await plugin.change_source(
            matcher, SimpleNamespace(available=True, result=value), manager
        )
    matcher.finish.assert_awaited_once_with("无效的序号。")
    assert manager.current_index == 0


@pytest.mark.parametrize("fetcher_type", [AHF, FGF])
@pytest.mark.parametrize(
    "html", ["<p>No content</p>", '<figure class="aligncenter"></figure>']
)
async def test_old_fetchers_handle_missing_download(fetcher_type, html):
    fetcher = fetcher_type()
    async with httpx.AsyncClient(
        base_url=fetcher.base_url,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=html)),
    ) as client:
        fetcher._client = client
        assert await fetcher.fetch(TorrentTag(game_name="Game", url="/game")) is None


@pytest.mark.parametrize(
    ("fetcher_type", "html", "link"),
    [
        (FGF, '<a href="magnet:?xt=test">Download</a>', "magnet:?xt=test"),
        (
            AHF,
            (
                '<figure class="aligncenter"><a href="/download">Download</a></figure>'
                '<figure class="aligncenter"></figure>'
            ),
            "https://www.aimhaven.com/download",
        ),
    ],
)
async def test_old_fetchers_handle_missing_metadata(fetcher_type, html, link):
    fetcher = fetcher_type()
    async with httpx.AsyncClient(
        base_url=fetcher.base_url,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=html)),
    ) as client:
        fetcher._client = client
        resource = await fetcher.fetch(TorrentTag(game_name="Game", url="/game"))
    assert resource is not None
    assert resource.magnet == link
    assert resource.size == "Unknown"
    assert resource.last_update == "Unknown"


@pytest.mark.parametrize("fetcher_type", [AHF, FGF])
@pytest.mark.parametrize("operation", ["search", "fetch"])
async def test_old_fetchers_report_http_failure(fetcher_type, operation):
    fetcher = fetcher_type()
    async with httpx.AsyncClient(
        base_url=fetcher.base_url,
        transport=httpx.MockTransport(lambda _: httpx.Response(503)),
    ) as client:
        fetcher._client = client
        argument = (
            "Game"
            if operation == "search"
            else TorrentTag(game_name="Game", url="/game")
        )
        with pytest.raises(RequestError):
            await getattr(fetcher, operation)(argument)
