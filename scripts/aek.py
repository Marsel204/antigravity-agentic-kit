#!/usr/bin/env python3
"""Source-tree / installed-bundle entry point; no pip installation required."""

import sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit("AEK requires Python 3.11 or newer.")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aek.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
