import asyncio
from pathlib import Path

from nonebot import get_driver, logger

from . import __main__

DRIVER = get_driver()
CONFIG_PATH = Path("./config/game_torrent.text")


def _read_source() -> int:
    try:
        index = int(CONFIG_PATH.read_text(encoding="utf-8").strip())
    except FileNotFoundError:
        return 0
    except (ValueError, OSError) as e:
        logger.warning(f"读取源配置失败，将使用默认源: {e}")
        return 0
    if not 0 <= index < len(__main__.g_source._list):
        logger.warning("源配置序号越界，将使用默认源")
        return 0
    return index


def _write_source() -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(str(__main__.g_source._index), encoding="utf-8")


@DRIVER.on_startup
async def check_source():
    """读取源配置；首次启动或配置损坏时使用默认源。"""
    __main__.g_source._index = await asyncio.to_thread(_read_source)
    logger.success(
        f"已加载当前源为: {__main__.g_source._list[__main__.g_source._index].fetch_name}"
    )


@DRIVER.on_shutdown
async def save_source():
    """保存当前源并关闭 HTTP 客户端。"""
    try:
        await asyncio.to_thread(_write_source)
        logger.success(
            f"已保存当前源为: {__main__.g_source._list[__main__.g_source._index].fetch_name}"
        )
    except OSError as e:
        logger.warning(f"保存源配置失败: {e}")
    finally:
        await asyncio.gather(*(fetcher.aclose() for fetcher in __main__.g_source._list))
