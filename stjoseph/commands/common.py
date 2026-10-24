from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any

import asyncclick as click

from stjoseph.api import constants, oauth2

if TYPE_CHECKING:
    from collections.abc import Callable


@click.group()
def cli() -> None:
    pass


def credentials_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Adds the --credentials, --token and --headless options and passes them to func as creds."""

    @click.option(
        "-c",
        "--credentials",
        type=click.Path(dir_okay=False, path_type=Path),
        default=constants.CREDENTIALS_FILE,
        envvar="STJOSEPH_CREDENTIALS",
        show_envvar=True,
        help="The path to the OAuth client secret file (only needed to create a new token)",
    )
    @click.option(
        "--token",
        type=click.Path(dir_okay=False, path_type=Path),
        default=constants.TOKEN_FILE,
        envvar="STJOSEPH_TOKEN",
        show_envvar=True,
        help="The path to the token file",
    )
    @click.option(
        "--headless",
        type=bool,
        is_flag=True,
        envvar="STJOSEPH_HEADLESS",
        show_envvar=True,
        help="Never open a browser or modify the token file; fail if the token cannot be refreshed",
    )
    @wraps(func)
    def wrapper(*args: Any, credentials: Path, token: Path, headless: bool, **kwargs: Any) -> Any:  # noqa: ANN401
        return func(*args, creds=oauth2.CredentialsManager(credentials, token, headless=headless), **kwargs)

    return wrapper
