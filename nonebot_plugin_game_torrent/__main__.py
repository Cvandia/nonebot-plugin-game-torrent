"""
File: __main__.py
    Description: 插件主要mathcer逻辑
"""

from dataclasses import dataclass
from typing import Any

from nonebot import on_command, require
from nonebot.adapters import Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

require("nonebot_plugin_waiter")

from typing import TYPE_CHECKING

from nonebot_plugin_waiter import waiter

# 新的源在此导入
from .fetcher import AHF, FGF, BaseFetcher

if TYPE_CHECKING:
    from .fetcher import TorrentTag


@dataclass
class Source:
    """
    搜索器列表
    """

    _list: list[BaseFetcher] = None
    _index: int = 0


g_source = Source(_list=[AHF(), FGF()], _index=0)  # 在此添加新的源

match = on_command("种子", aliases={"游戏种子", "游戏下载"}, priority=25)
show_source = on_command("显示源", aliases={"显示种子库", "全部源"}, priority=26)
change_source = on_command("更换源", aliases={"更换种子库", "换源"}, priority=27)


async def get_user_input(matcher: Matcher, prompt: str, timeout: int = 60) -> str:
    """
    使用waiter获取用户输入
    """
    await matcher.send(prompt)

    @waiter(waits=["message"], keep_session=True)
    async def wait_for_user_input(event: Event):
        return event.get_plaintext()

    user_input = await wait_for_user_input.wait(timeout=timeout)
    if not user_input:
        await matcher.finish("输入超时。")
    elif user_input.lower() in ["取消", "cancel", "quit", "q"]:
        await matcher.finish("操作已取消。")
    return user_input


@match.handle()
async def event_matcher(
    matcher: Matcher,
    search_args: Any = CommandArg(),  # noqa
):
    game_name = str(search_args).strip()
    if not game_name:
        game_name = await get_user_input(
            matcher, "请输入您想搜索的游戏名称。(仅支持英文搜索)"
        )

    fetcher = g_source._list[g_source._index]
    await match.send("正在搜索...")
    tags: list[TorrentTag] = await fetcher.search(keyword=game_name)  # 搜索游戏

    if not tags:
        await match.finish("未找到游戏。")

    await match.send(
        "以下是搜索结果：\n"
        + "\n".join(f"{index+1}. {tag}\n" for index, tag in enumerate(tags))
    )
    user_input = await get_user_input(matcher, "请输入您想下载的游戏的序号。")

    if not user_input.isdigit() or int(user_input) > len(tags) or int(user_input) < 1:
        await matcher.finish("无效的序号。")

    game_resource = await fetcher.fetch(tags[int(user_input) - 1])
    if not game_resource:
        await match.finish("未找到游戏资源。")
    if not game_resource.is_hacked:
        await match.send("警告：该游戏不是破解版，请合法下载。")
    await match.finish(str(game_resource))
    # 上传种子文件至群文件（未完成）


@show_source.handle()
async def _(matcher: Matcher):
    await matcher.finish(
        "当前源："
        + g_source._list[g_source._index].fetch_name
        + "\n"
        + "源列表：\n"
        + "\n".join(
            f"{index+1}. {fetcher.fetch_name}"
            for index, fetcher in enumerate(g_source._list)
        )
    )


@change_source.handle()
async def _(matcher: Matcher, source_index: Any = CommandArg()):  # noqa
    _index = str(source_index).strip()
    if not _index:
        _index = await get_user_input(matcher, "请输入您想更换的源的序号。")
    if not _index.isdigit() or int(_index) > len(g_source._list) or int(_index) < 1:
        await matcher.finish("无效的序号。")
    g_source._index = int(_index) - 1
    await matcher.finish("已更换至" + g_source._list[g_source._index].fetch_name)
