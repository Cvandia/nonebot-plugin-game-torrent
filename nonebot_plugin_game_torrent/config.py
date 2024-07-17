from typing import Optional

from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel):

    proxy_url: Optional[str] = None
    proxy_auth: Optional[str] = None


plugin_config = Config(**get_driver().config.dict())
