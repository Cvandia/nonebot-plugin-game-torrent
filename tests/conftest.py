import nonebot
from nonebot.adapters.console import Adapter
from nonebug import NONEBOT_START_LIFESPAN

nonebot.init(driver="~none")
nonebot.get_driver().register_adapter(Adapter)
nonebot.load_plugin("nonebot_plugin_game_torrent")


def pytest_configure(config):
    # 抓取器测试不启动机器人，避免读写用户的源配置文件。
    config.stash[NONEBOT_START_LIFESPAN] = False
