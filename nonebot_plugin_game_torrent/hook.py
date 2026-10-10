import asyncio

from nonebot import get_driver

from .source import get_source_manager

DRIVER = get_driver()


@DRIVER.on_startup
async def check_source():
    """读取源配置；首次启动或配置损坏时使用默认源。"""
    manager = await asyncio.to_thread(get_source_manager)
    await manager.load()


@DRIVER.on_shutdown
async def save_source():
    """保存当前源并关闭 HTTP 客户端。"""
    manager = await asyncio.to_thread(get_source_manager)
    try:
        await manager.save()
    finally:
        await manager.aclose()
