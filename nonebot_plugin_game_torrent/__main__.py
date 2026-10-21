"""
File: __main__.py
    Description: 插件主要mathcer逻辑
"""

from nonebot import get_driver, logger, require
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
    aliases={"搜索游戏", "搜游戏"},
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
source_list = on_alconna(Alconna("游戏源"), use_cmd_start=True)
source_change = on_alconna(
    Alconna("切换源", Args["source_index?#编号或名称", str]),
    aliases={"切换游戏源"},
    use_cmd_start=True,
)
game_help = on_alconna(Alconna("游戏帮助"), use_cmd_start=True)


def command_example(command: str) -> str:
    prefixes = get_driver().config.command_start
    prefix = "/" if "/" in prefixes else next(iter(sorted(prefixes)), "")
    return prefix + command


def source_menu(manager: SourceManager) -> str:
    return (
        f"当前游戏源：{manager.current.fetch_name}\n"
        + "\n".join(
            f"{index + 1}. {fetcher.fetch_name}"
            for index, fetcher in enumerate(manager.fetchers)
        )
        + f"\n发送 {command_example('切换源 ' + str(len(manager.fetchers)))}"
        + f" 或 {command_example('切换源 ' + manager.fetchers[-1].fetch_name)} 切换。"
        + "\n切换会对整个机器人生效。"
    )


@game_help.handle()
async def show_help(matcher: Matcher):
    await matcher.finish(
        "游戏查询指令\n"
        f"{command_example('搜游戏 游戏名')}：搜索游戏，回复编号获取链接\n"
        f"{command_example('游戏源')}：查看当前网站和网站列表\n"
        f"{command_example('切换源 编号或名称')}：切换网站\n"
        "等待输入时，发送“取消”结束；60 秒未回复自动结束。\n"
        "Aimhaven、Fitgirl 请用英文游戏名；切换网站对整个机器人生效。"
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
        await matcher.finish(
            f"等待回复超时，已结束。发送 {command_example('游戏帮助')} 查看用法。"
        )
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
            matcher, "请回复游戏名（Aimhaven、Fitgirl 请用英文），或发送“取消”。"
        )

    fetcher = source_manager.current
    await matcher.send(f"正在 {fetcher.fetch_name} 搜索“{game_name}”…")
    try:
        tags: list[TorrentTag] = await fetcher.search(keyword=game_name)  # 搜索游戏
    except RequestError as e:
        logger.warning(f"{fetcher.fetch_name} 搜索失败: {e}")
        await matcher.finish(
            f"当前网站搜索失败，请稍后重试，或发送 {command_example('游戏源')} 更换网站。"
        )

    if not tags:
        await matcher.finish(
            f"未找到“{game_name}”。请换个关键词，或发送 {command_example('游戏源')} 更换网站。"
        )

    await matcher.send(
        f"{fetcher.fetch_name} 搜索结果：\n"
        + "\n".join(f"{index + 1}. {tag.game_name}" for index, tag in enumerate(tags))
    )
    user_input = await get_user_input(
        matcher, f"回复编号 1–{len(tags)} 获取链接，或发送“取消”（60 秒内）。"
    )

    if not user_input.isdecimal() or not 1 <= int(user_input) <= len(tags):
        await matcher.finish(
            f"编号无效，请重新发送 {command_example('搜游戏 ' + game_name)}，并选择 1–{len(tags)}。"
        )
    try:
        game_resource = await fetcher.fetch(tags[int(user_input) - 1])
    except RequestError as e:
        logger.warning(f"{fetcher.fetch_name} 获取资源失败: {e}")
        await matcher.finish("当前网站获取链接失败，请稍后重试或切换网站。")
    if not game_resource:
        await matcher.finish(
            "该页面没有可用的公开资源链接，请换一个结果或切换网站重新搜索。"
        )
    if not game_resource.is_hacked:
        await matcher.send("请按游戏发布页面的说明获取资源。")
    if plugin_config.magnet_to_qrcode:
        # 生成二维码
        await UniMessage.image(raw=url2qrcode_bytes(game_resource.magnet)).finish()
    await matcher.finish(str(game_resource))
    # 上传种子文件至群文件（未完成）


@source_list.handle()
@source.assign("show")
async def show_source(
    matcher: Matcher,
    source_manager: Annotated[SourceManager, Depends(get_source_manager)],
):
    await matcher.finish(source_menu(source_manager))


@source_change.handle()
@source.assign("change")
async def change_source(
    matcher: Matcher,
    source_index: Match[str],
    source_manager: Annotated[SourceManager, Depends(get_source_manager)],
):
    index = source_index.result if source_index.available else None
    logger.debug(f"匹配到指令：{source_index.result}, 源序号：{index}")
    if not index:
        index = await get_user_input(
            matcher,
            source_menu(source_manager) + "\n请回复编号或网站名称，或发送“取消”。",
        )
    index = index.strip()
    selected = next(
        (
            i
            for i, fetcher in enumerate(source_manager.fetchers)
            if fetcher.fetch_name.casefold() == index.casefold()
        ),
        None,
    )
    if (
        selected is None
        and index.isdecimal()
        and 1 <= int(index) <= len(source_manager.fetchers)
    ):
        selected = int(index) - 1
    if selected is None:
        await matcher.finish(
            f"来源无效，请发送 {command_example('游戏源')} 查看编号和名称。"
        )
    source_manager.select(selected)
    await matcher.finish("已更换至" + source_manager.current.fetch_name)
