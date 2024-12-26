import datetime
from pathlib import Path
from typing import Final

import pytz

MAX_RETRY: Final[int] = 2

MAX_FIELD_LEN: Final[int] = 25

GCLOUD_DATE_FMT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"

CREDENTIALS_FILE: Final[Path] = Path(Path.cwd(), "credentials.json").resolve()

TOKEN_FILE: Final[Path] = Path(Path.cwd(), "token.json").resolve()

DATE_FMT: Final[str] = "%Y-%m-%d"
DATE_TIME_FMT: Final[str] = "%Y-%m-%d %H:%M"

SATURDAY_EVENING_MASS: Final[tuple[int, int]] = (17, 30)  # 5:30 PM

NO_OP: Final[str] = "NOOP"

LIVE_STREAMING_URL_FMT: Final[str] = "https://studio.youtube.com/video/{VIDEO_ID}/livestreaming"

DEFAULT_TIMEZONE: Final[datetime.tzinfo] = pytz.timezone("America/New_York")

MAX_DESCRIPTION_LENGTH: Final[int] = 5000  # the description maximum length
