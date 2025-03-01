"""Game specific code."""
from __future__ import annotations

from typing import Iterable

GAME_LENGTH = 150  # seconds

# Marker sizes are in mm
MARKER_SIZES: dict[Iterable[int], int] = {
    # TODO: FIXME
    range(28): 150,  # 0 - 27 for arena boundary
    range(28, 200): 80,  # Everything else is a token
}
