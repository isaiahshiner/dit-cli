"""Misc global configuration options"""

from dataclasses import dataclass
from typing import Optional

DIT_FILEPATH: Optional[str] = None


@dataclass
class CodeLocation:
    """Represents a position in a memoryview of code
    view[pos] will always be the current char
    line is incremented at every \n and col is reset to 0"""

    pos: int
    col: int
    line: int
