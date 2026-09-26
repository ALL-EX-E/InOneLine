from __future__ import annotations

from .auction_session import AuctionSessionMixin
from .wheel import WheelMixin


class AuctionMixin(AuctionSessionMixin, WheelMixin):
    """Compatibility mixin combining auction-session and wheel storage."""

    pass
