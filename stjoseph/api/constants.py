import datetime as dt
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo

MAX_RETRIES: Final[int] = 2

MAX_FIELD_LEN: Final[int] = 25

GCLOUD_DATE_FMT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"

CREDENTIALS_FILE: Final[Path] = Path(Path.cwd(), "credentials.json").resolve()

TOKEN_FILE: Final[Path] = Path(Path.cwd(), "token.json").resolve()

DATE_FMT: Final[str] = "%Y-%m-%d"

DATE_TIME_FMT: Final[str] = "%Y-%m-%d %H:%M"

SATURDAY_EVENING_MASS: Final[tuple[int, int]] = (17, 30)  # 5:30 PM

CHRISTMAS_PAGEANT_TIME: Final[tuple[int, int]] = (16, 00)  # 4 PM
CHRISTMAS_PAGEANT_DATE: Final[tuple[int, int]] = (12, 24)  # 12/24

NO_OP: Final[str] = "NOOP"

LIVE_STREAMING_URL_FMT: Final[str] = "https://studio.youtube.com/video/{VIDEO_ID}/livestreaming"

DEFAULT_TIMEZONE: Final[dt.tzinfo] = ZoneInfo("America/New_York")

MAX_DESCRIPTION_LENGTH: Final[int] = 5000  # the description maximum length

YOUTUBE_RECORDING_LOCATION_DESCRIPTION: Final[str] = "St Joseph Roman Catholic Church Comly Road, Lincoln Park, NJ"
YOUTUBE_CAPTION_CERTIFICATION: Final[str] = (
    "Caption certification: This content has never aired on television in the U.S."
)
YOUTUBE_NO_ALTERED_CONTENT_STATEMENT: Final[str] = "No altered content."
