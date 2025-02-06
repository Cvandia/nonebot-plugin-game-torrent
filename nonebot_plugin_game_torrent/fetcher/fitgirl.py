"""
Time: 2025/1/16

File: fitgirl.py
    Description: fitgirl 网站, 继承自BaseFetcher, 主要实现了search和fetch方法

Author: Cvandia
"""

import re
from typing import Optional

from bs4 import BeautifulSoup
from httpx import HTTPError

from ..exception import RequestError  # noqa: TID252
from .base_model import BaseFetcher, TorrentResource, TorrentTag


class FitgirlFetcher(BaseFetcher):
    """
    fitgirl 网站, 继承自BaseFetcher, 主要实现了search和fetch方法
    """

    fetch_name = "Fitgirl"
    base_url = "https://fitgirl-repacks.site/"

    async def search(self, keyword: str) -> list[TorrentTag]:
        try:
            rsp = await self.client.get("", params={"s": keyword})
        except HTTPError as e:
            raise RequestError(f"fitgirl search error: {e}") from e
        soup = BeautifulSoup(rsp.text, "html.parser")
        tags = []
        for h1 in soup.find_all("h1", class_="entry-title"):
            a = h1.find("a")
            tags.append(TorrentTag(game_name=a.text, url=a["href"]))
        return tags

    async def fetch(self, tag: TorrentTag) -> Optional[TorrentResource]:
        try:
            rsp = await self.client.get(tag.url)
        except HTTPError as e:
            raise RequestError(f"fitgirl fetch error: {e}") from e
        soup = BeautifulSoup(rsp.text, "html.parser")
        magnet = soup.find("a", href=lambda href: href and href.startswith("magnet:"))
        size_element = soup.find(string=re.compile(r"Original Size:")).find_next(
            "strong"
        )
        size = size_element.text if size_element else "Unknown"
        last_update = soup.find("time", class_="entry-date").text
        return TorrentResource(
            game_name=tag.game_name,
            magnet=magnet["href"],
            size=size,
            last_update=last_update,
            is_hacked=True,
        )
