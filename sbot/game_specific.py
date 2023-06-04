"""Game specific code."""
from typing import Dict, Iterable

MARKER_SIZES: Dict[Iterable[int], int] = {
    range(28): 200,  # 0 - 27 for arena boundary
    range(28, 100): 80,  # Everything else is a token
}
