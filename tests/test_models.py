import datetime as dt
from unittest.mock import patch

from stjoseph.api import constants, models

_TZ = constants.DEFAULT_TIMEZONE


def _local(year: int, month: int, day: int, hour: int, minute: int) -> dt.datetime:
    return dt.datetime(year, month, day, hour, minute, tzinfo=_TZ).astimezone(dt.UTC)


def _stream(
    scheduled_start: dt.datetime | None,
    actual_start: dt.datetime | None = None,
    title: str = "title",
) -> models.LiveStream:
    actual_end = actual_start + dt.timedelta(hours=1) if actual_start else None
    return models.LiveStream("id", title, "description", None, scheduled_start, actual_start, actual_end)


def test_get_aired_start_returns_scheduled_time_on_aired_date() -> None:
    # Scheduled for Oct 10 5:30 PM but went live on Oct 17 at 5:27 PM.
    stream = _stream(_local(2026, 10, 10, 17, 30), _local(2026, 10, 17, 17, 27))
    aired = stream.get_aired_start()
    assert aired is not None
    assert (aired.year, aired.month, aired.day, aired.hour, aired.minute) == (2026, 10, 17, 17, 30)


def test_get_aired_start_is_none_when_aired_on_scheduled_date() -> None:
    stream = _stream(_local(2026, 10, 10, 17, 30), _local(2026, 10, 10, 17, 27))
    assert stream.get_aired_start() is None


def test_get_aired_start_is_none_when_never_aired() -> None:
    assert _stream(_local(2026, 10, 10, 17, 30)).get_aired_start() is None


def test_get_aired_start_uses_title_date_when_schedule_was_moved() -> None:
    # Labeled October 10, but the schedule was moved to Oct 17 5:00 PM and it went live Oct 17 at 5:25 PM.
    stream = _stream(
        _local(2026, 10, 17, 17, 0),
        _local(2026, 10, 17, 17, 25),
        title="Mass October 10, 2026 - 5:30 PM: Twenty-eighth Sunday in Ordinary Time",
    )
    aired = stream.get_aired_start()
    assert aired is not None
    assert (aired.year, aired.month, aired.day, aired.hour, aired.minute) == (2026, 10, 17, 17, 30)


def test_get_aired_start_is_none_when_title_matches_aired_date() -> None:
    # Scheduled for Saturday, but already retitled to the Sunday it aired.
    stream = _stream(
        _local(2026, 8, 8, 17, 30),
        _local(2026, 8, 9, 10, 14),
        title="Mass August 9, 2026 - 10:15 AM: Nineteenth Sunday in Ordinary Time",
    )
    assert stream.get_aired_start() is None


def test_get_title_start_parses_legacy_title() -> None:
    stream = _stream(None, title="Mass July 13, 2024 - 5:30PM")
    assert stream.get_title_start() == dt.datetime(2024, 7, 13, 17, 30)  # noqa: DTZ001


def test_is_stale() -> None:
    with patch.object(models.USCCB, "today", return_value=dt.date(2026, 10, 23)):
        assert _stream(_local(2026, 10, 17, 17, 30)).is_stale()
        assert not _stream(_local(2026, 10, 24, 17, 30)).is_stale()
        assert not _stream(_local(2026, 10, 17, 17, 30), _local(2026, 10, 17, 17, 27)).is_stale()


def test_get_title_start_is_none_for_unparseable_title() -> None:
    assert _stream(None, title="Mass Auigust 14, 2021 - 5:30 PM").get_title_start() is None


def test_get_title_start_parses_lowercase_meridiem() -> None:
    stream = _stream(None, title="Mass February 21, 2021 - 12:00pm")
    assert stream.get_title_start() == dt.datetime(2021, 2, 21, 12, 0)  # noqa: DTZ001
