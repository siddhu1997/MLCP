from __future__ import annotations

import os # pyright: ignore[reportUnusedImport]
from pathlib import Path

from mlcp.common.logger import get_logger


from dotenv import load_dotenv

log = get_logger("ENV")

def load_local_env() -> None:
    """
    Load .env.local if it exists, without overriding already-set env vars.
    """
    env_path = Path(__file__).resolve().parents[3] / ".env.local"
    if env_path.exists():
        load_dotenv(env_path, override=False)
        log.info("Loaded local environment variables from %s", env_path)
    else:
        log.info("No local environment file found at %s", env_path)

# Load immediately when this module is imported
load_local_env()
