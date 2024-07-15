from nonebot.matcher import Matcher
from nonebot.rule import Rule
from nonebot.typing import T_State
from nonebot.params import CommandArg
from nonebot.adapters import Bot, Event
from httpx import AsyncClient
from typing import Optional, Union, Any
from fake_useragent import UserAgent
from .__init__ import match


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

    @classmethod
    def fetch(cls, keyword: str) -> None:
        raise NotImplementedError


@match.handle()
async def event_matcher(bot: Bot, event: Event, matcher: Matcher, search_args: Any = CommandArg()):
    if game_name := str(search_args) or event.get_plaintext().split():
        await matcher.send(f"Searching for {game_name}...")
    else:
        await matcher.finish("Please input the game name you want to search.")

    fetch_response: dict = await GameFetcher.fetch(game_name)
    if fetch_response['game_name']:

    else:
        await matcher.finish("No game found.")

@match.got("game_name", prompt="Please input the index for the game you want to search.")
async def handle_game_name(bot: Bot, event: Event, state: T_State):
    game_name = state["game_name"]
    await match.send(f"Searching for {game_name}...")
    fetch_response: dict = await GameFetcher.fetch(game_name)
    if fetch_response['game_name']:
        await match.send(fetch_response['game_name'])
    else:
        await match.finish("No game found.")