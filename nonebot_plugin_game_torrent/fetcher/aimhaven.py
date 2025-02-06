"""
Time: 2025/1/15

File: aimehaven.py
    Description: Aimehaven.com 爬取类, 继承自BaseFetcher, 主要实现了search和fetch方法

Author: Cvandia
"""

from typing import Optional

from bs4 import BeautifulSoup
from httpx import HTTPError

from ..exception import RequestError  # noqa: TID252
from .base_model import BaseFetcher, TorrentResource, TorrentTag


class AimhavenFetcher(BaseFetcher):
    """
    游戏种子资源搜索器
    """

    base_url = "https://www.aimhaven.com/"
    fetch_name = "Aimhaven"

    async def search(self, keyword: str) -> list[TorrentTag]:
        """
        搜索游戏

        - keyword: 搜索关键字
        """
        try:
            response = await self.client.get("", params={"s": keyword})
        except HTTPError as e:
            raise RequestError(f"Aimhaven search error: {e}") from e
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
        try:
            response = await self.client.get(tag.url)
        except HTTPError as e:
            raise RequestError(f"Aimhaven fetch error: {e}") from e
        soup = BeautifulSoup(response.text, "html.parser")
        if figcaption := soup.find("figcaption", class_="wp-element-caption"):
            size = figcaption.get_text().strip("Size: ")
        if (i := soup.find("i", class_="fa fa-calendar")) and (
            span := i.find_next("span")
        ):
            time = span.get_text().strip()
        is_hacked = True
        if soup.find("mark", class_="has-vivid-red-color"):
            is_hacked = False
        figure = soup.find("figure", class_="aligncenter")
        if a := figure.find("a"):
            if figure := figure.find_next("figure", class_="aligncenter"):
                a = figure.find("a")
            magnet = a["href"]
            return TorrentResource(
                game_name=tag.game_name,
                magnet=magnet,  # type: ignore
                size=size,
                last_update=time,
                is_hacked=is_hacked,
            )
        return None
