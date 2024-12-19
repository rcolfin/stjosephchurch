"""Extracts and saves a file from a streaming video feed."""

from __future__ import annotations

import logging
import sys

from stjoseph.commands import cli

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)-12s: %(levelname)-8s\t%(message)s", stream=sys.stdout
    )

    cli(_anyio_backend="asyncio")


if __name__ == "__main__":
    main()
