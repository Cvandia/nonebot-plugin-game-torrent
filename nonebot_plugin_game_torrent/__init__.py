import contextlib

from . import __main__, hook  # noqa: F401
from .config import Config

with contextlib.suppress(Exception):
    from nonebot.plugin import PluginMetadata, inherit_supported_adapters

    __plugin_meta__ = PluginMetadata(
        name="游戏种子搜索",
        description="搜索游戏种子资源",
        usage="搜索游戏 [游戏名称]",
        homepage="https://github.com/Cvandia/nonebot-plugin-game-torrent",
        config=Config,
        type="application",
        supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
        extra={"author": "Cvandia", "email": "1141538825@qq.com"},
    )
