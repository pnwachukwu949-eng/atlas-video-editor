#!/usr/bin/env python3
"""CLI entry for Atlas speak."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from atlas.acquisition.speak import main
if __name__ == "__main__":
    raise SystemExit(main())
