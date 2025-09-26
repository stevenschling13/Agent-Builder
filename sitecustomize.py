"""Ensure src/ directory is importable without installation."""
from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
_src_str = str(_src)
if _src.exists() and _src_str not in sys.path:
    sys.path.insert(0, _src_str)
