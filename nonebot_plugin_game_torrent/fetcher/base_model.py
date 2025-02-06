"""
File: base_model.py
    Description: 基础爬取class, 后续的爬取类都继承这个类
"""

from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from fake_useragent import UserAgent
from httpx import AsyncClient
from pydantic import BaseModel, Field

from ..config import plugin_config  # noqa: TID252

torrent_send_format = plugin_config.torrent_send_format


class TorrentResource(BaseModel):
    """
    游戏种子资源
    """

    # 游戏名称
    game_name: str

    # 游戏种子链接
    magnet: str

    # 游戏大小
    size: str

    # 最新更新上传时间
    last_update: str

    # torrent资源种子的文件路劲
    torrent_path: str = Field(default="")

    # 是否为破解版
    is_hacked: bool = True

    def _to_str(self) -> str:
        return torrent_send_format.format(**self.dict())

    def __str__(self) -> str:
        return self._to_str()


class TorrentTag(BaseModel):
    """
    种子资源的标签
    """

    # 游戏名称
    game_name: str
    # 游戏链接，可以是搜索链接，也可以是具体的游戏链接
    url: str

    def __str__(self) -> str:
        return f"name:{self.game_name}\nlink:{self.url}\n"


class BaseFetcher(ABC):
    # 爬取源的名称
    fetch_name: str
    # 爬取源的基础url
    base_url: str
    _client: Optional[AsyncClient] = None

    _headers: ClassVar[dict] = {
        "User-Agent": UserAgent().chrome,
    }

    @property
    def client(self) -> AsyncClient:
        if not self._client:
            self._client = AsyncClient(
                base_url=self.base_url or "",
                headers=self._headers,
                timeout=100,
            )
        return self._client

    @classmethod
    def set_headers(cls, key: str, value: str) -> None:
        """
        设置请求头
        """
        cls._headers[key] = value

    @abstractmethod
    async def search(self, keyword: str) -> list[TorrentTag]:
        """
        搜索种子资源

        - keyword: 搜索关键字
        """

    @abstractmethod
    async def fetch(self, tag: TorrentTag) -> Optional[TorrentResource]:
        """
        获取种子资源
        """
