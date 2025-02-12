"""
File: __main__.py
    Description: 插件主要mathcer逻辑
"""

from dataclasses import dataclass

from nonebot import logger, require
from nonebot.adapters import Event
from nonebot.matcher import Matcher

require("nonebot_plugin_waiter")
require("nonebot_plugin_alconna")

from typing import TYPE_CHECKING

from nonebot_plugin_alconna import (
    Alconna,
    Args,
    Match,
    MultiVar,
    Subcommand,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_waiter import waiter

from .config import plugin_config
from .exception import RequestError

# 新的源在此导入
from .fetcher import AHF, FGF, BaseFetcher
from .utils import url2qrcode_bytes

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

match = on_alconna(
    Alconna(
        "游戏搜索",
        Args["content?#内容", MultiVar("str")],
    ),
    aliases={"搜索游戏"},
    use_cmd_start=True,
)
source = on_alconna(
    Alconna(
        "种子源",
        Subcommand(
            "show",
            alias={"显示", "查看"},
        ),
        Subcommand(
            "change",
            Args["source_index?#源序号", str],
            alias={"更换", "切换"},
        ),
    ),
    aliases={"源"},
    use_cmd_start=True,
)


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
    content: Match[tuple[str, ...]],
):
    game_name = " ".join(content.result) if content.available else None
    logger.debug(f"匹配到指令：{content.result}, 游戏名称：{game_name}")
    if not game_name:
        game_name = await get_user_input(
            matcher, "请输入您想搜索的游戏名称。(仅支持英文搜索)"
        )

    fetcher = g_source._list[g_source._index]
    await match.send("正在搜索...")
    try:
        tags: list[TorrentTag] = await fetcher.search(keyword=game_name)  # 搜索游戏
    except RequestError as e:
        await match.finish(f"搜索失败: {e}")

    if not tags:
        await match.finish("未找到游戏。")

    await match.send(
        "以下是搜索结果：\n"
        + "\n".join(f"{index + 1}. {tag}\n" for index, tag in enumerate(tags))
    )
    user_input = await get_user_input(matcher, "请输入您想下载的游戏的序号。")

    if not user_input.isdigit() or int(user_input) > len(tags) or int(user_input) < 1:
        await matcher.finish("无效的序号。")
    try:
        game_resource = await fetcher.fetch(tags[int(user_input) - 1])
    except RequestError as e:
        await match.finish(f"获取游戏资源失败: {e}")
    if not game_resource:
        await match.finish("未找到游戏资源。")
    if not game_resource.is_hacked:
        await match.send("警告：该游戏不是破解版，请合法下载。")
    if plugin_config.magnet_to_qrcode:
        # 生成二维码
        await UniMessage.image(raw=url2qrcode_bytes(game_resource.magnet)).finish()
    await match.finish(str(game_resource))
    # 上传种子文件至群文件（未完成）


@source.assign("show")
async def _(matcher: Matcher):
    await matcher.finish(
        "当前源："
        + g_source._list[g_source._index].fetch_name
        + "\n"
        + "源列表：\n"
        + "\n".join(
            f"{index + 1}. {fetcher.fetch_name}"
            for index, fetcher in enumerate(g_source._list)
        )
    )


@source.assign("change")
async def _(matcher: Matcher, source_index: Match[tuple[str, ...]]):
    index = source_index.result if source_index.available else None
    logger.debug(f"匹配到指令：{source_index.result}, 源序号：{index}")
    if not index:
        index = await get_user_input(matcher, "请输入您想更换的源的序号。")
    if not index.isdigit() or int(index) > len(g_source._list) or int(index) < 1:
        await matcher.finish("无效的序号。")
    g_source._index = int(index) - 1
    await matcher.finish("已更换至" + g_source._list[g_source._index].fetch_name)
