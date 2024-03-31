import contextlib
from nonebot import on_command
from .utils import event_matcher

with contextlib.suppress(Exception):
    from nonebot.plugin import PluginMetadata

    __plugin_meta__ = PluginMetadata(
        name="nonebot_plugin_game_torrent",
        description="A plugin for nonebot2 to get torrent games.",
        usage="Just type the game name you want to search.",
        homepage="https://github.com/Cvandia/nonebot-plugin-game-torrent",
        supported_adapters=None,
        extra={"author": "Cvandia", "email": "1141538825@qq.com"},
    )

on_command('种子',aliases={'游戏种子','游戏下载'},priority=5,handlers=[event_matcher])