from __future__ import annotations

import importlib.metadata

from stjoseph import api

# set the version number within the package using importlib
try:
    __version__: str | None = importlib.metadata.version("stjoseph")
except importlib.metadata.PackageNotFoundError:
    # package is not installed
    __version__ = None


__all__ = ["__version__", "api"]
