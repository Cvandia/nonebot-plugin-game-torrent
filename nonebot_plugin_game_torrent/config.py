from typing import Optional

from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):

    proxy_url: Optional[str] = None
    proxy_auth: Optional[str] = None
    torrent_path: Optional[str] = None
    torrent_send_format: str = (
        "game: {game_name}\nsize: {size}\nlast_update: {last_update}\nmagnet: {magnet}\n"
    )
    # 是否上传种子文件至群文件
    upload_torrent: bool = False


plugin_config = get_plugin_config(Config)
