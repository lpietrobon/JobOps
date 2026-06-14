from .greenhouse import GreenhouseFetcher
from .lever import LeverFetcher
from .ashby import AshbyFetcher
from .static_sources import CustomURLFetcher
FETCHERS = {f.name: f for f in [GreenhouseFetcher(), LeverFetcher(), AshbyFetcher(), CustomURLFetcher()]}
