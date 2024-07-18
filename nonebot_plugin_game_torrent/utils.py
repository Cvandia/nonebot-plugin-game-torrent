from typing import List, Optional

from fake_useragent import UserAgent
from httpx import AsyncClient
from pydantic import BaseModel, Extra

from .config import plugin_config


class TorrentResource(BaseModel, extra=Extra.allow):
    """
    ### 游戏种子资源
    """

    # 游戏名称
    game_name: str

    # 游戏种子链接
    magnet: str

    # 游戏大小F
    size: str

    # 最新更新上传时间
    last_update: str

    # torrent资源种子的文件路劲
    torrent_path: str

    # 是否为破解版
    is_hacked: bool

    def _to_str(self) -> str:
        return plugin_config.torrent_send_format.format(**self.dict())

    def __str__(self) -> str:
        return self._to_str()


class TorrentTag(BaseModel):
    """
    种子资源的标签
    """

    game_name: str
    url: str


class BaseFetcher:
    fetch_name: str = ""
    base_url: str = ""
    _client: Optional[AsyncClient] = None

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": UserAgent().chrome,
        }

    @property
    def client(self) -> AsyncClient:
        if not self._client:
            self._client = AsyncClient(
                base_url=self.base_url or "",
                headers=self.headers,
                timeout=100,
            )
        return self._client

    def set_headers(self, key: str, value: str) -> None:
        """
        设置请求头
        """
        self.headers[key] = value


class GameFetcher(BaseFetcher):
    base_url = "https://www.aimhaven.com/"

    async def search(self, keyword: str) -> List[TorrentTag]:
        self.fetch_name = keyword
        raise NotImplementedError

    async def fetch(self, tag: TorrentTag) -> TorrentResource:
        raise NotImplementedError
