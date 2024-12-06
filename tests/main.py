from datetime import datetime

import pytest
from nonebot.adapters.console import Message, MessageEvent, User
from nonebug import App


@pytest.mark.asyncio
async def test_torrent_search(app: App):
    import nonebot_plugin_game_torrent

    event = MessageEvent(
        time=datetime.now(),
        self_id="test",
        message=Message("种子"),
        user=User(id="test_user"),
    )
    async with app.test_matcher(nonebot_plugin_game_torrent.match) as ctx:
        bot = ctx.create_bot()
        ctx.receive_event(bot, event)
        ctx.should_call_send("请输入您想搜索的游戏名称。(仅支持英文搜索)")
