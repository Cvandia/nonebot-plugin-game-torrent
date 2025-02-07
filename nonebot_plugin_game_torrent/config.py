"""
File: config.py
    Description: 插件配置文件
"""

from typing import Optional

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    torrent_send_format: Optional[str] = (
        "game: {game_name}\nsize: {size}\nlast_update: {last_update}\nmagnet: {magnet}\n"
    )

    # TODO 是否上传种子文件至群文件

    magnet_to_qrcode: bool = False


plugin_config = get_plugin_config(Config)
