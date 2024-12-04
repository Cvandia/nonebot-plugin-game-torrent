from typing import Optional

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from httpx import AsyncClient
from pydantic import BaseModel

from .config import plugin_config


class TorrentResource(BaseModel):
    """
    ### 游戏种子资源
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
    torrent_path: str

    # 是否为破解版
    is_hacked: bool = False

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

    def __str__(self) -> str:
        return f"{self.game_name}\n{self.url}"


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
    """
    游戏种子资源搜索器
    """

    base_url = "https://www.aimhaven.com/"

    async def search(self, keyword: str) -> list[TorrentTag]:
        """
        搜索游戏

        - keyword: 搜索关键字
        """
        self.fetch_name = keyword
        response = await self.client.get("", params={"s": keyword})
        soup = BeautifulSoup(response.text, "html.parser")
        tags = []
        if h2s := soup.find_all("h2", class_="title front-view-title"):
            for h2 in h2s:
                a = h2.find("a")
                tags.append(TorrentTag(game_name=a["title"], url=a["href"]))
        return tags

    async def fetch(self, tag: TorrentTag) -> Optional[TorrentResource]:
        """
        获取种子资源

        - tag: 种子资源标签
        """
        response = await self.client.get(tag.url)
        soup = BeautifulSoup(response.text, "html.parser")
        if figcaption := soup.find("figcaption", class_="wp-element-caption"):
            size = figcaption.get_text().strip("Size: ")
        if (i := soup.find("i", class_="fa fa-calendar")) and (
            span := i.find_next("span")
        ):
            time = span.get_text().strip()
        if figure := soup.find("figure", class_="aligncenter size-full"):
            if a := figure.find_next("a"):
                magnet = a["href"]  # type: ignore
            return TorrentResource(
                game_name=tag.game_name,
                magnet=magnet,  # type: ignore
                size=size,
                last_update=time,
                is_hacked=False,  # 未完成
            )
        return None
