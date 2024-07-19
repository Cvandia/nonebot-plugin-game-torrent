import contextlib

from .config import Config
from .match import *

with contextlib.suppress(Exception):
    from nonebot.plugin import PluginMetadata

    __plugin_meta__ = PluginMetadata(
        name="nonebot_plugin_game_torrent",
        description="A plugin for nonebot2 to get torrent games.",
        usage="Just type the game name you want to search.",
        homepage="https://github.com/Cvandia/nonebot-plugin-game-torrent",
        config=Config,
        type="application",
        supported_adapters=None,
        extra={"author": "Cvandia", "email": "1141538825@qq.com"},
    )
