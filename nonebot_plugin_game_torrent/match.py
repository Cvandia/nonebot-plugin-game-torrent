from typing import Any

from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.rule import Rule
from nonebot.typing import T_State

from .config import plugin_config
from .utils import GameFetcher

match = on_command("种子", aliases={"游戏种子", "游戏下载"}, priority=25)


@match.handle()
async def event_matcher(
    bot: Bot, event: Event, matcher: Matcher, search_args: Any = CommandArg()
):
    if game_name := str(search_args) or event.get_plaintext().split():
        await matcher.send(f"Searching for {game_name}...")
    else:
        await matcher.finish("Please input the game name you want to search.")

    fetch_response: dict = await GameFetcher.fetch(game_name)
    if fetch_response["game_name"]:
        pass
    else:
        await matcher.finish("No game found.")


@match.got(
    "game_name", prompt="Please input the index for the game you want to search."
)
async def handle_game_name(bot: Bot, event: Event, state: T_State):
    game_name = state["game_name"]
    await match.send(f"Searching for {game_name}...")
    fetch_response: dict = await GameFetcher.fetch(game_name)
    if fetch_response["game_name"]:
        await match.send(fetch_response["game_name"])
    else:
        await match.finish("No game found.")
