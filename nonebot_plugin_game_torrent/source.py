"""源管理及持久化，与命令处理和生命周期注册解耦。"""

import asyncio
from functools import lru_cache
from pathlib import Path

from nonebot import logger, require

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

from .fetcher import AHF, FGF, ZYKF, BaseFetcher


class SourceManager:
    def __init__(
        self,
        fetchers: tuple[BaseFetcher, ...],
        config_file: Path,
        legacy_file: Path | None = None,
    ) -> None:
        if not fetchers:
            raise ValueError("源列表不能为空")
        self._fetchers = fetchers
        self._index = 0
        self._config_file = config_file
        self._legacy_file = legacy_file

    @property
    def fetchers(self) -> tuple[BaseFetcher, ...]:
        return self._fetchers

    @property
    def current(self) -> BaseFetcher:
        return self._fetchers[self._index]

    @property
    def current_index(self) -> int:
        return self._index

    def select(self, index: int) -> None:
        """按从零开始的序号切换源。"""
        if not 0 <= index < len(self._fetchers):
            raise ValueError("源序号越界")
        self._index = index

    def _write_index(self, index: int) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(str(index), encoding="utf-8")

    def _read_index(self) -> int:
        migrated = False
        try:
            try:
                text = self._config_file.read_text(encoding="utf-8")
            except FileNotFoundError:
                if self._legacy_file is None:
                    return 0
                text = self._legacy_file.read_text(encoding="utf-8")
                migrated = True
            index = int(text.strip())
        except FileNotFoundError:
            return 0
        except (ValueError, OSError) as e:
            logger.warning(f"读取源配置失败，将使用默认源: {e}")
            return 0
        if not 0 <= index < len(self._fetchers):
            logger.warning("源配置序号越界，将使用默认源")
            return 0
        if migrated:
            try:
                self._write_index(index)
                logger.info("旧源配置已迁移至 localstore，原文件保留")
            except OSError as e:
                logger.warning(f"迁移源配置失败，本次仍使用旧配置: {e}")
        return index

    async def load(self) -> None:
        self.select(await asyncio.to_thread(self._read_index))
        logger.success(f"已加载当前源为: {self.current.fetch_name}")

    async def save(self) -> None:
        try:
            await asyncio.to_thread(self._write_index, self._index)
            logger.success(f"已保存当前源为: {self.current.fetch_name}")
        except OSError as e:
            logger.warning(f"保存源配置失败: {e}")

    async def aclose(self) -> None:
        await asyncio.gather(*(fetcher.aclose() for fetcher in self._fetchers))


@lru_cache(maxsize=1)
def get_source_manager() -> SourceManager:
    """提供插件级共享实例，供依赖注入和生命周期回调使用。"""
    return SourceManager(
        fetchers=(AHF(), FGF(), ZYKF()),
        config_file=store.get_plugin_config_file("game_torrent.text"),
        # 仅用于兼容旧版本；所有写入均使用 localstore 返回的位置。
        legacy_file=Path("config/game_torrent.text"),
    )
