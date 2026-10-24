import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from stjoseph.api import oauth2
from stjoseph.api.services.channel import Channel


def _http_error(status: int, reason: str) -> HttpError:
    content = {"error": {"code": status, "message": reason, "errors": [{"reason": reason, "message": reason}]}}
    return HttpError(Mock(status=status, reason=reason), json.dumps(content).encode())


def _wrapped_creds(manager: oauth2.CredentialsManager, error: RefreshError) -> Credentials:
    creds = Mock()
    creds.refresh.side_effect = error
    return manager._wrap_creds(creds)  # noqa: SLF001


@pytest.mark.parametrize(
    ("status", "reason", "expected"),
    [
        (401, "authError", True),
        (403, "insufficientPermissions", True),
        (403, "quotaExceeded", False),
        (403, "forbidden", False),
        (404, "notFound", False),
    ],
)
def test_is_invalid_token_error(status: int, reason: str, expected: bool) -> None:
    assert Channel._is_invalid_token_error(_http_error(status, reason)) is expected  # noqa: SLF001


def test_refresh_keeps_token_on_transient_failure(tmp_path: Path) -> None:
    token = tmp_path / "token.json"
    token.write_text("{}")
    manager = oauth2.CredentialsManager(tmp_path / "credentials.json", token)
    creds = _wrapped_creds(manager, RefreshError("unavailable", retryable=True))
    with pytest.raises(RefreshError):
        creds.refresh(Mock())
    assert token.exists()


def test_refresh_removes_revoked_token(tmp_path: Path) -> None:
    token = tmp_path / "token.json"
    token.write_text("{}")
    creds = _wrapped_creds(oauth2.CredentialsManager(tmp_path / "credentials.json", token), RefreshError("revoked"))
    with pytest.raises(RefreshError):
        creds.refresh(Mock())
    assert not token.exists()


def test_headless_never_modifies_token(tmp_path: Path) -> None:
    token = tmp_path / "token.json"
    token.write_text("{}")
    manager = oauth2.CredentialsManager(tmp_path / "credentials.json", token, headless=True)
    creds = _wrapped_creds(manager, RefreshError("revoked"))
    with pytest.raises(RefreshError):
        creds.refresh(Mock())
    manager.write_token("changed")
    assert token.read_text() == "{}"


def test_headless_does_not_start_browser_flow(tmp_path: Path) -> None:
    manager = oauth2.CredentialsManager(tmp_path / "credentials.json", tmp_path / "token.json", headless=True)
    with pytest.raises(oauth2.AuthenticationRequiredError):
        manager.create_oauth_credentials(Channel.SCOPES)
