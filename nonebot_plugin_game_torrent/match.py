from typing import Any, List

from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.rule import Rule
from nonebot.typing import T_State

from .config import plugin_config
from .utils import GameFetcher, TorrentResource, TorrentTag

match = on_command("种子", aliases={"游戏种子", "游戏下载"}, priority=25)


@match.handle()
async def event_matcher(
    bot: Bot,
    state: T_State,
    event: Event,
    matcher: Matcher,
    search_args: Any = CommandArg(),
):
    if game_name := str(search_args) or event.get_plaintext().split():
        matcher.set_arg("game_name", game_name)
        state["Fetcher"] = GameFetcher()


@match.got("game_name", prompt="Please input the name of the game you want to search.")
async def handle_game_name(
    bot: Bot, event: Event, state: T_State, game_name: str = ArgPlainText()
):

    # 取消继续对话（未完成）
    game_fetcher: GameFetcher = state["Fetcher"]
    game_name = state["game_name"]
    tags = await game_fetcher.search(game_name)
    if not tags:
        await match.finish("No game found.")
    state["tags"] = tags
    send_message = "\n".join([str(i) for i in tags])
    await match.finish(send_message)


@match.got(
    "game_index", prompt="Please input the index of the game you want to download."
)
async def handle_game_index(
    bot: Bot, event: Event, state: T_State, index: str = ArgPlainText()
):

    # 取消继续对话（未完成）
    game_fetcher: GameFetcher = state["Fetcher"]
    game_index = state["game_index"]
    tags: List[TorrentTag] = state["tags"]
    game_resource = await game_fetcher.fetch(tags[game_index])
    if not game_resource.is_hacked:
        await match.send(
            "warning: This game is not a cracked version, please download it legally."
        )
        await match.finish(str(game_resource))
    else:
        await match.finish(str(game_resource))

    # 上传种子文件至群文件（未完成）
