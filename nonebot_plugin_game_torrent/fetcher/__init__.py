from .aimhaven import AimhavenFetcher as AHF
from .base_model import BaseFetcher, TorrentResource, TorrentTag
from .fitgirl import FitgirlFetcher as FGF
from .gamer520 import Gamer520Fetcher as G520F
from .zyk123 import Zyk123Fetcher as ZYKF

__all__ = [
    "AHF",
    "FGF",
    "G520F",
    "ZYKF",
    "BaseFetcher",
    "TorrentResource",
    "TorrentTag",
]
