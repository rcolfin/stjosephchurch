import contextlib
import logging
from functools import wraps
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Final

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from stjoseph.api import constants

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


def _is_refresh_exception(e: BaseException) -> bool:
    """Returns True if the exception is a RefreshError exception."""
    return isinstance(e, RefreshError)


class CredentialsManager:
    def __init__(self, creds_file: PathLike, token_file: PathLike) -> None:
        self._creds_file = Path(creds_file)
        self._token_file = Path(token_file)
        self.__token_file_ctime = self._token_file.stat().st_ctime if self._token_file.exists() else None

    @property
    def creds_file(self) -> Path:
        return self._creds_file

    @property
    def token_file(self) -> Path:
        return self._token_file

    def write_token(self, data: str) -> None:
        self._token_file.write_text(data)

    def invalidate_token(self) -> bool:
        """Invalidates the token"""
        if self._token_file.exists():
            logger.info("Removing %s", self._token_file)
            self._token_file.unlink()
            return True
        return False

    def is_token_changed(self) -> bool:
        """Determines if the token has changed."""
        token_file_ctime = self._token_file.stat().st_ctime if self._token_file.exists() else None
        return token_file_ctime != self.__token_file_ctime

    @retry(
        retry=retry_if_exception(_is_refresh_exception),
        wait=wait_exponential(),
        stop=stop_after_attempt(constants.MAX_RETRIES),
    )
    def create_oauth_credentials(self, scopes: list[str]) -> Credentials:
        """Creates an instance of OAuth 2.0 Credentials"""
        creds = None
        if self._token_file.exists():
            with contextlib.suppress(ValueError):
                logger.info("Authenticating %s", self._token_file)
                creds = self._wrap_creds(Credentials.from_authorized_user_file(str(self._token_file), scopes))

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing credentials")
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(self._creds_file), scopes)
                creds = self._wrap_creds(flow.run_local_server(port=0), save=True)

        return creds

    def _wrap_creds(self, creds: Credentials, save: bool = False) -> Credentials:
        refresh_orig: Final[Callable[[Request], None]] = creds.refresh

        def save_token() -> None:
            logger.info("Saving token to %s", self._token_file)
            self.write_token(creds.to_json())

        @wraps(creds.refresh)
        def refresh(request: Request) -> None:
            self.invalidate_token()
            refresh_orig(request)
            save_token()

        creds.refresh = refresh

        if save:
            save_token()

        return creds
