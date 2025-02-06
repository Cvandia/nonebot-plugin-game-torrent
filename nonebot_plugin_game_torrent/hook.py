from pathlib import Path

from nonebot import get_driver, logger

from . import __main__

DRIVER = get_driver()


@DRIVER.on_startup
async def check_source():
    """
    检查源
    """

    config_path = Path("./config/game_torrent.text")
    if not config_path.exists():
        with Path.open(config_path, mode="w") as f:
            f.write("0")
    with Path.open(config_path, mode="r") as f:
        __main__.g_source._index = int(f.read())
        logger.success(
            f"已加载当前源为: {__main__.g_source._list[__main__.g_source._index].fetch_name}"
        )


@DRIVER.on_shutdown
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
