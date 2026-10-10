# ruff: noqa: S101

import asyncio
from contextlib import AsyncExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from nonebot.dependencies import Dependent
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher

from nonebot_plugin_game_torrent import __main__ as plugin
from nonebot_plugin_game_torrent import source
from nonebot_plugin_game_torrent.fetcher import AHF, FGF, ZYKF
from nonebot_plugin_game_torrent.source import SourceManager


def test_manager_requires_sources(tmp_path):
    with pytest.raises(ValueError, match="源列表不能为空"):
        SourceManager((), tmp_path / "source.text")


@pytest.mark.parametrize("index", [-1, 3])
def test_selection_is_validated(tmp_path, index):
    manager = SourceManager((AHF(), FGF(), ZYKF()), tmp_path / "source.text")
    with pytest.raises(ValueError, match="源序号越界"):
        manager.select(index)
    assert manager.current_index == 0


async def test_show_source_uses_injected_manager(tmp_path):
    manager = SourceManager((AHF(), FGF(), ZYKF()), tmp_path / "source.text")
    manager.select(2)
    matcher = SimpleNamespace(finish=AsyncMock(side_effect=FinishedException))
    with pytest.raises(FinishedException):
        await plugin.show_source(matcher, manager)
    matcher.finish.assert_awaited_once_with(
        "当前源：123资源库\n源列表：\n1. Aimhaven\n2. Fitgirl\n3. 123资源库"
    )


@pytest.mark.parametrize("existing", [None, "0", "invalid"])
async def test_legacy_migration_only_when_new_file_absent(tmp_path, existing):
    legacy = tmp_path / "old.text"
    legacy.write_text("2", encoding="utf-8")
    config = tmp_path / "localstore" / "game_torrent.text"
    if existing is not None:
        config.parent.mkdir()
        config.write_text(existing, encoding="utf-8")
    manager = SourceManager((AHF(), FGF(), ZYKF()), config, legacy)
    await manager.load()
    assert manager.current_index == (2 if existing is None else 0)
    assert await asyncio.to_thread(legacy.read_text, encoding="utf-8") == "2"
    if existing is None:
        assert await asyncio.to_thread(config.read_text, encoding="utf-8") == "2"


async def test_manager_restores_saved_selection(tmp_path):
    config = tmp_path / "source.text"
    first = SourceManager((AHF(), FGF()), config)
    first.select(1)
    await first.save()
    second = SourceManager((AHF(), FGF()), config)
    await second.load()
    assert second.current_index == 1


def test_provider_uses_localstore_plugin_override(tmp_path, monkeypatch):
    # 验证真实 localstore API 按插件配置获取路径，而不是硬编码工作目录。
    monkeypatch.setattr(
        source.store.plugin_config,
        "localstore_plugin_config_dir",
        {"nonebot_plugin_game_torrent": tmp_path},
    )
    source.get_source_manager.cache_clear()
    try:
        manager = source.get_source_manager()
        assert manager is source.get_source_manager()
        manager.select(2)
        asyncio.run(manager.save())
        assert (tmp_path / "game_torrent.text").read_text(encoding="utf-8") == "2"
    finally:
        source.get_source_manager.cache_clear()


async def test_nonebot_resolves_manager_dependency(tmp_path, monkeypatch):
    monkeypatch.setattr(
        source.store.plugin_config,
        "localstore_plugin_config_dir",
        {"nonebot_plugin_game_torrent": tmp_path},
    )
    source.get_source_manager.cache_clear()
    try:
        handler = Dependent.parse(
            call=plugin.show_source, allow_types=Matcher.HANDLER_PARAM_TYPES
        )
        async with AsyncExitStack() as stack:
            values = await handler.solve(
                matcher=Matcher(), stack=stack, dependency_cache={}
            )
        assert values["source_manager"] is source.get_source_manager()
    finally:
        source.get_source_manager.cache_clear()
