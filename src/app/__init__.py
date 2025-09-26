"""Application entry package."""
from __future__ import annotations

import sys
from pathlib import Path

_src_path = Path(__file__).resolve().parent.parent
_src_str = str(_src_path)
if _src_str not in sys.path:
    sys.path.append(_src_str)
