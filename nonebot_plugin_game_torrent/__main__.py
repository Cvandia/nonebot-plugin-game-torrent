"""
File: __main__.py
    Description: 插件主要mathcer逻辑
"""

from nonebot import logger, require
from nonebot.adapters import Event
from nonebot.matcher import Matcher
from nonebot.params import Depends

require("nonebot_plugin_waiter")
require("nonebot_plugin_alconna")

from typing import TYPE_CHECKING, Annotated

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
from .source import SourceManager, get_source_manager
from .utils import url2qrcode_bytes

if TYPE_CHECKING:
    from .fetcher import TorrentTag


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
    user_input = user_input.strip() if user_input else ""
    if not user_input:
        await matcher.finish("输入超时。")
    elif user_input.lower() in ["取消", "cancel", "quit", "q"]:
        await matcher.finish("操作已取消。")
    return user_input


@match.handle()
async def event_matcher(
    matcher: Matcher,
    content: Match[tuple[str, ...]],
    source_manager: Annotated[SourceManager, Depends(get_source_manager)],
):
    game_name = " ".join(content.result) if content.available else None
    logger.debug(f"匹配到指令：{content.result}, 游戏名称：{game_name}")
    if not game_name:
        game_name = await get_user_input(
            matcher, "请输入您想搜索的游戏名称。(Aimhaven、Fitgirl 请使用英文)"
        )

    fetcher = source_manager.current
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

    if not user_input.isdecimal() or not 1 <= int(user_input) <= len(tags):
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
async def show_source(
    matcher: Matcher,
    source_manager: Annotated[SourceManager, Depends(get_source_manager)],
):
    await matcher.finish(
        "当前源："
        + source_manager.current.fetch_name
        + "\n"
        + "源列表：\n"
        + "\n".join(
            f"{index + 1}. {fetcher.fetch_name}"
            for index, fetcher in enumerate(source_manager.fetchers)
        )
    )


@source.assign("change")
async def change_source(
    matcher: Matcher,
    source_index: Match[str],
    source_manager: Annotated[SourceManager, Depends(get_source_manager)],
):
    index = source_index.result if source_index.available else None
    logger.debug(f"匹配到指令：{source_index.result}, 源序号：{index}")
    if not index:
        index = await get_user_input(matcher, "请输入您想更换的源的序号。")
    index = index.strip()
    if not index.isdecimal() or not 1 <= int(index) <= len(source_manager.fetchers):
        await matcher.finish("无效的序号。")
    source_manager.select(int(index) - 1)
    await matcher.finish("已更换至" + source_manager.current.fetch_name)
