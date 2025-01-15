import contextlib

from nonebot import get_driver, logger

from . import __main__
from .config import Config

with contextlib.suppress(Exception):
    from nonebot.plugin import PluginMetadata

    __plugin_meta__ = PluginMetadata(
        name="游戏种子搜索",
        description="搜索游戏种子资源",
        usage="种子 [游戏名称]",
        homepage="https://github.com/Cvandia/nonebot-plugin-game-torrent",
        config=Config,
        type="application",
        supported_adapters=None,
        extra={"author": "Cvandia", "email": "1141538825@qq.com"},
    )

driver = get_driver()


@driver.on_startup
async def check_source():
    """
    检查源
    """
    from pathlib import Path

    config_path = Path("./config/game_torrent.text")
    if not config_path.exists():
        with Path.open(config_path, mode="w") as f:
            f.write("0")
    with Path.open(config_path, mode="r") as f:
        __main__.g_source._index = int(f.read())
        logger.success(
            f"已加载当前源为: {__main__.g_source._list[__main__.g_source._index].fetch_name}"
        )


@driver.on_shutdown
async def save_source():
    """
    保存源
    """
    from pathlib import Path

    config_path = Path("./config/game_torrent.text")
    with Path.open(config_path, mode="w") as f:
        f.write(str(__main__.g_source._index))
        logger.success(
            f"已保存当前源为: {__main__.g_source._list[__main__.g_source._index].fetch_name}"
        )
