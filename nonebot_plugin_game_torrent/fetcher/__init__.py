from .aimhaven import AimhavenFetcher as AHF
from .base_model import BaseFetcher, TorrentResource, TorrentTag
from .fitgirl import FitgirlFetcher as FGF

__all__ = ["AHF", "FGF", "BaseFetcher", "TorrentResource", "TorrentTag"]
