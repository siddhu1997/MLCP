from __future__ import annotations

import os
from pathlib import Path


def ensure_workspace() -> Path:
    """
    Create the shared workspace folders if missing.
    Returns the root path. No-op if already present.
    """
    root = Path(os.getenv("DATA_ROOT", "/workspace"))
    for sub in ("layers", "archive", "logs", "db"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
