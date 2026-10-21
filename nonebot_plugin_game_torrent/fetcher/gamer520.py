"""Gamer520 的公开搜索结果和正文资源链接。"""

import re
from typing import ClassVar
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from httpx import HTTPError

from ..exception import RequestError  # noqa: TID252
from .base_model import BaseFetcher, TorrentResource, TorrentTag


class Gamer520Fetcher(BaseFetcher):
    """读取公开页面，不解析登录、付费或加密跳转后的内容。"""

    fetch_name = "Gamer520"
    base_url = "https://www.gamer520.com/"
    _site_hosts: ClassVar[set[str]] = {"www.gamer520.com", "gamer520.com"}
    _share_hosts: ClassVar[set[str]] = {
        "pan.baidu.com",
        "pan.quark.cn",
        "www.alipan.com",
        "www.aliyundrive.com",
        "www.123pan.com",
        "www.123865.com",
        "www.123912.com",
        "cloud.189.cn",
    }

    @classmethod
    def _is_site_url(cls, url: str) -> bool:
        parsed = urlsplit(url)
        return parsed.scheme in {"http", "https"} and parsed.hostname in cls._site_hosts

    async def search(self, keyword: str) -> list[TorrentTag]:
        if not keyword.strip():
            return []
        try:
            response = await self.client.get("", params={"s": keyword})
            response.raise_for_status()
        except HTTPError as e:
            raise RequestError(f"gamer520 search error: {e}") from e
        if not self._is_site_url(str(response.url)):
            raise RequestError("gamer520 search redirected outside the source site")

        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        seen = set()
        for link in soup.select(
            ".entry-title a[href], .post-title a[href], "
            ".excerpt h2 a[href], h2.item-heading a[href]"
        ):
            name = link.get_text(" ", strip=True)
            url = urljoin(str(response.url), str(link["href"]).strip())
            parsed = urlsplit(url)
            url = urlunsplit(parsed._replace(fragment=""))
            if (
                not name
                or not self._is_site_url(url)
                or (parsed.path == "/" and not parsed.query.startswith("p="))
                or parsed.path.startswith(("/category/", "/tag/", "/author/"))
                or url in seen
            ):
                continue
            seen.add(url)
            results.append(TorrentTag(game_name=name, url=url))
        return results

    @classmethod
    def _is_resource_url(cls, url: str) -> bool:
        parsed = urlsplit(url)
        return (parsed.scheme == "magnet" and bool(parsed.query)) or (
            parsed.scheme in {"http", "https"} and parsed.hostname in cls._share_hosts
        )

    @classmethod
    def _free_download_entry(cls, soup: BeautifulSoup, page_url: str) -> str:
        """返回页面公开标注免费的官方入口，不跟踪下载跳转。"""
        page = urlsplit(page_url)
        match = re.fullmatch(r"/(\d+)\.html", page.path)
        post_id = match[1] if match else parse_qs(page.query).get("p", [""])[0]
        if not post_id.isascii() or not post_id.isdecimal():
            return ""
        for widget in soup.select(".widget-pay"):
            price = widget.select_one(".pay--rateinfo .price")
            if price is None or price.get_text(strip=True) != "免费":
                continue
            for link in widget.select(".pay--content a.go-downblank[href]"):
                url = urljoin(page_url, str(link["href"]).strip())
                parsed = urlsplit(url)
                if (
                    cls._is_site_url(url)
                    and parsed.path == "/go"
                    and parse_qs(parsed.query) == {"post_id": [post_id]}
                ):
                    return url
        return ""

    async def fetch(self, tag: TorrentTag) -> TorrentResource | None:
        url = urljoin(self.base_url, tag.url)
        if not self._is_site_url(url):
            raise RequestError("gamer520 fetch URL is outside the source site")
        try:
            response = await self.client.get(url)
            response.raise_for_status()
        except HTTPError as e:
            raise RequestError(f"gamer520 fetch error: {e}") from e
        if not self._is_site_url(str(response.url)):
            raise RequestError("gamer520 fetch redirected outside the source site")

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select_one(".entry-content, .wp-posts-content")
        if content is None:
            content = soup.select_one(".article-content")
        text = content.get_text(" ", strip=True) if content is not None else ""
        candidates = [
            urljoin(str(response.url), str(link["href"]).strip())
            for link in (content.select("a[href]") if content is not None else [])
        ]
        # 有些文章直接展示链接文本，而没有生成 a 标签。
        candidates.extend(
            re.findall(r"(?:https?://|magnet:\?)[^\s<>\"'，。；）]+", text)
        )
        resources = [url for url in candidates if self._is_resource_url(url)]
        entry = self._free_download_entry(soup, str(response.url))
        if not resources and not entry:
            return None
        download = next(
            (url for url in resources if urlsplit(url).scheme == "magnet"),
            resources[0] if resources else entry,
        )
        size = re.search(
            r"(?:容量|游戏大小|文件大小)\s*[:：]?\s*(\d+(?:\.\d+)?\s*[KMGT](?:i?B)?)\b",
            text,
            re.IGNORECASE,
        )
        date = soup.select_one('meta[property="article:modified_time"][content]')
        if date is None:
            date = soup.select_one('meta[property="article:published_time"][content]')
        last_update = str(date["content"]) if date else ""
        if not last_update:
            time = soup.select_one(".entry-meta time, .article-header time")
            if time is not None:
                last_update = str(time.get("datetime") or time.get_text(strip=True))
        return TorrentResource(
            game_name=tag.game_name,
            magnet=download,
            size=size[1] if size else "Unknown",
            last_update=last_update or "Unknown",
        )
