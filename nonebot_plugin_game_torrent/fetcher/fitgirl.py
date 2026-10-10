"""
Time: 2025/1/16

File: fitgirl.py
    Description: fitgirl 网站, 继承自BaseFetcher, 主要实现了search和fetch方法

Author: Cvandia
"""

import re
from urllib.parse import urljoin

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
            rsp.raise_for_status()
        except HTTPError as e:
            raise RequestError(f"fitgirl search error: {e}") from e
        soup = BeautifulSoup(rsp.text, "html.parser")
        return [
            TorrentTag(
                game_name=a.get_text(strip=True), url=urljoin(str(rsp.url), a["href"])
            )
            for a in soup.select("h1.entry-title a[href]")
        ]

    async def fetch(self, tag: TorrentTag) -> TorrentResource | None:
        try:
            rsp = await self.client.get(tag.url)
            rsp.raise_for_status()
        except HTTPError as e:
            raise RequestError(f"fitgirl fetch error: {e}") from e
        soup = BeautifulSoup(rsp.text, "html.parser")
        magnet = soup.find("a", href=lambda href: href and href.startswith("magnet:"))
        if magnet is None:
            return None
        size_label = soup.find(string=re.compile(r"Original Size:"))
        size_element = size_label.find_next("strong") if size_label else None
        size = size_element.text if size_element else "Unknown"
        date_element = soup.find("time", class_="entry-date")
        last_update = date_element.get_text(strip=True) if date_element else "Unknown"
        return TorrentResource(
            game_name=tag.game_name,
            magnet=magnet["href"],
            size=size,
            last_update=last_update,
            is_hacked=True,
        )
