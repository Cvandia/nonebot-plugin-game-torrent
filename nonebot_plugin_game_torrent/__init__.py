import contextlib

from . import match  # noqa
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
