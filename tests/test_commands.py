# ruff: noqa: S101

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from nonebot.exception import FinishedException

from nonebot_plugin_game_torrent import __main__ as plugin
from nonebot_plugin_game_torrent.exception import RequestError
from nonebot_plugin_game_torrent.fetcher import (
    AHF,
    FGF,
    G520F,
    ZYKF,
    TorrentResource,
    TorrentTag,
)
from nonebot_plugin_game_torrent.source import SourceManager


@pytest.mark.parametrize("command", ["搜游戏", "游戏搜索", "搜索游戏"])
def test_search_commands_preserve_multiword_names(command):
    result = plugin.match.command().parse(f"/{command} Ori and the Blind Forest")
    assert result.matched
    assert result.all_matched_args["content"] == (
        "Ori",
        "and",
        "the",
        "Blind",
        "Forest",
    )


@pytest.mark.parametrize(
    ("matcher", "command", "expected"),
    [
        (plugin.source_list, "/游戏源", {}),
        (plugin.game_help, "/游戏帮助", {}),
        (plugin.source_change, "/切换源 Gamer520", {"source_index": "Gamer520"}),
        (plugin.source_change, "/切换游戏源 4", {"source_index": "4"}),
        (plugin.source_change, "/切换源", {}),
        (plugin.source, "/种子源 show", {}),
        (plugin.source, "/源 查看", {}),
        (plugin.source, "/种子源 change 4", {"source_index": "4"}),
        (plugin.source, "/源 切换 4", {"source_index": "4"}),
    ],
)
def test_new_and_legacy_command_parsing(matcher, command, expected):
    result = matcher.command().parse(command)
    assert result.matched
    assert result.all_matched_args == expected


@pytest.fixture
def matcher():
    return SimpleNamespace(
        send=AsyncMock(), finish=AsyncMock(side_effect=FinishedException)
    )


@pytest.mark.parametrize("selection", ["4", "Gamer520", "gamer520", "  Gamer520  "])
async def test_select_source_by_number_or_name(tmp_path, matcher, selection):
    manager = SourceManager((AHF(), FGF(), ZYKF(), G520F()), tmp_path / "source.text")
    with pytest.raises(FinishedException):
        await plugin.change_source(
            matcher, SimpleNamespace(available=True, result=selection), manager
        )
    assert isinstance(manager.current, G520F)


async def test_source_without_argument_prompts_with_menu(
    tmp_path, matcher, monkeypatch
):
    manager = SourceManager((AHF(), G520F()), tmp_path / "source.text")
    prompt = AsyncMock(return_value="Gamer520")
    monkeypatch.setattr(plugin, "get_user_input", prompt)
    with pytest.raises(FinishedException):
        await plugin.change_source(
            matcher, SimpleNamespace(available=False, result=None), manager
        )
    assert "1. Aimhaven\n2. Gamer520" in prompt.call_args.args[1]
    assert isinstance(manager.current, G520F)


@pytest.mark.parametrize("prefix", ["!", ""])
async def test_help_uses_configured_prefix(matcher, monkeypatch, prefix):
    monkeypatch.setattr(
        plugin,
        "get_driver",
        lambda: SimpleNamespace(config=SimpleNamespace(command_start={prefix})),
    )
    with pytest.raises(FinishedException):
        await plugin.show_help(matcher)
    message = matcher.finish.call_args.args[0]
    assert f"{prefix}搜游戏 游戏名" in message
    assert f"{prefix}切换源 编号或名称" in message
    assert "/游戏源" not in message


@pytest.mark.parametrize("reply", [None, "取消", " Q "])
async def test_waiter_timeout_and_cancel_finish_session(matcher, monkeypatch, reply):
    wait = AsyncMock(return_value=reply)
    monkeypatch.setattr(
        plugin, "waiter", lambda **_kwargs: lambda _func: SimpleNamespace(wait=wait)
    )
    with pytest.raises(FinishedException):
        await plugin.get_user_input(matcher, "请输入")
    message = matcher.finish.call_args.args[0]
    assert ("超时" if reply is None else "操作已取消") in message
    wait.assert_awaited_once_with(timeout=60)


async def test_search_select_and_get_link(tmp_path, matcher, monkeypatch):
    fetcher = G520F()
    manager = SourceManager((fetcher,), tmp_path / "source.text")
    tags = [
        TorrentTag(game_name="奥日", url="/1.html"),
        TorrentTag(game_name="奥日2", url="/2.html"),
    ]
    resource = TorrentResource(
        game_name="奥日2",
        magnet="https://example.com/game",
        size="Unknown",
        last_update="Unknown",
    )
    search = AsyncMock(return_value=tags)
    fetch = AsyncMock(return_value=resource)
    monkeypatch.setattr(fetcher, "search", search)
    monkeypatch.setattr(fetcher, "fetch", fetch)
    monkeypatch.setattr(plugin, "get_user_input", AsyncMock(return_value="2"))
    monkeypatch.setattr(plugin.plugin_config, "magnet_to_qrcode", False)
    with pytest.raises(FinishedException):
        await plugin.event_matcher(
            matcher, SimpleNamespace(available=True, result=("Ori", "2")), manager
        )
    search.assert_awaited_once_with(keyword="Ori 2")
    fetch.assert_awaited_once_with(tags[1])
    matcher.send.assert_any_await("Gamer520 搜索结果：\n1. 奥日\n2. 奥日2")
    matcher.finish.assert_awaited_once_with(str(resource))


@pytest.mark.parametrize("failure", [True, False])
async def test_search_failure_or_no_results_offer_next_step(
    tmp_path, matcher, monkeypatch, failure
):
    fetcher = G520F()
    search = (
        AsyncMock(side_effect=RequestError("HTTP 403"))
        if failure
        else AsyncMock(return_value=[])
    )
    monkeypatch.setattr(fetcher, "search", search)
    with pytest.raises(FinishedException):
        await plugin.event_matcher(
            matcher,
            SimpleNamespace(available=True, result=("奥日",)),
            SourceManager((fetcher,), tmp_path / "source.text"),
        )
    message = matcher.finish.call_args.args[0]
    assert "/游戏源" in message
    assert "HTTP" not in message
