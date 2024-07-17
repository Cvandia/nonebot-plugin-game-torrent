from typing import Optional

from fake_useragent import UserAgent
from httpx import AsyncClient


class BaseFetcher:
    name: str = ""
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

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class GameFetcher(BaseFetcher):
    name = "game"
    base_url = "https://www.1377x.to/sort-category-search/"

    async def fetch(self, keyword: str) -> dict:
        async with self.client as client:
            response = await client.get(params={"search": keyword})
            return response.json()
