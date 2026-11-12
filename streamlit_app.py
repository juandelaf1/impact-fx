"""
Streamlit Community Cloud entrypoint.

This wrapper allows deploying from the repository root (default main file
`streamlit_app.py`) while keeping the actual app in `frontend/app.py`.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"

# Ensure `from services...` / `from components...` imports in frontend/app.py work.
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

runpy.run_path(str(FRONTEND_DIR / "app.py"), run_name="__main__")
