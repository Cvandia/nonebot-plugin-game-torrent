from .aimhaven import AimhavenFetcher as AHF
from .base_model import BaseFetcher, TorrentResource, TorrentTag
from .fitgirl import FitgirlFetcher as FGF
from .zyk123 import Zyk123Fetcher as ZYKF

__all__ = ["AHF", "FGF", "ZYKF", "BaseFetcher", "TorrentResource", "TorrentTag"]
