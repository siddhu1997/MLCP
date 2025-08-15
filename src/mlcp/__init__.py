"""MLCP top-level package."""
__all__ = ["__version__"]
__version__ = "0.0.1"

from mlcp.common import env  # pyright: ignore[reportUnusedImport] # noqa: F401  # ensures .env.local is loaded
