"""123资源库的公开搜索结果和游戏下载链接。"""

import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from httpx import HTTPError

from ..exception import RequestError  # noqa: TID252
from .base_model import BaseFetcher, TorrentResource, TorrentTag


class Zyk123Fetcher(BaseFetcher):
    """搜索 123资源库，优先返回磁力链接，否则返回公开网盘链接。"""

    fetch_name = "123资源库"
    base_url = "https://www.123zyk.com/"

    async def search(self, keyword: str) -> list[TorrentTag]:
        if not keyword.strip():
            return []
        try:
            response = await self.client.get(
                "", params={"s": keyword, "type": "post"}, follow_redirects=True
            )
            response.raise_for_status()
        except HTTPError as e:
            raise RequestError(f"123zyk search error: {e}") from e

        soup = BeautifulSoup(response.text, "html.parser")
        tags = []
        seen = set()
        for link in soup.select("h2.item-heading a[href]"):
            name = link.get_text(" ", strip=True)
            url = urljoin(str(response.url), str(link["href"]).strip())
            parsed = urlsplit(url)
            if (
                not name
                or parsed.scheme not in {"http", "https"}
                or parsed.hostname not in {"www.123zyk.com", "123zyk.com"}
                or url in seen
            ):
                continue
            seen.add(url)
            tags.append(TorrentTag(game_name=name, url=url))
        return tags

    async def fetch(self, tag: TorrentTag) -> TorrentResource | None:
        try:
            response = await self.client.get(tag.url, follow_redirects=True)
            response.raise_for_status()
        except HTTPError as e:
            raise RequestError(f"123zyk fetch error: {e}") from e

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select_one(".wp-posts-content")
        if content is None:
            return None

        # 只读取正文中的资源链接，避免把广告、帮助或相关推荐当成下载地址。
        magnet = ""
        download = ""
        for link in content.select("a[href]"):
            url = urljoin(str(response.url), str(link["href"]).strip())
            parsed = urlsplit(url)
            if parsed.scheme == "magnet":
                magnet = url
                break
            if (
                not download
                and parsed.scheme in {"http", "https"}
                and parsed.hostname
                in {
                    "pan.123zyk.com",
                    "pan.quark.cn",
                    "pan.baidu.com",
                    "www.alipan.com",
                    "www.aliyundrive.com",
                    "www.123pan.com",
                    "www.123865.com",
                    "www.123912.com",
                }
            ):
                download = url
        if not (magnet or download):
            return None

        size_match = re.search(
            r"(?:容量|游戏大小|文件大小)\s*[:：]?\s*(\d+(?:\.\d+)?\s*[KMGT](?:i?B)?)\b",
            content.get_text(" ", strip=True),
            re.IGNORECASE,
        )
        last_update = "Unknown"
        modified = soup.select_one('meta[property="article:modified_time"]')
        published = soup.select_one('meta[property="article:published_time"]')
        date = modified if modified is not None else published
        if date and date.get("content"):
            last_update = str(date["content"])
        elif time := soup.select_one(".article-header time"):
            last_update = str(time.get("datetime") or time.get_text(strip=True))

        return TorrentResource(
            game_name=tag.game_name,
            magnet=magnet or download,
            size=size_match[1] if size_match else "Unknown",
            last_update=last_update or "Unknown",
        )
