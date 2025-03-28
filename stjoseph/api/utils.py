from __future__ import annotations

import datetime

import dateutil.tz

from stjoseph.api import constants, models


def parse_gcloud_datetime(date_string: str) -> datetime.datetime:
    """Parses a Google Cloud API Date String"""
    return datetime.datetime.strptime(date_string, constants.GCLOUD_DATE_FMT).replace(tzinfo=datetime.UTC)


def to_gcloud_datetime(dt: datetime.datetime) -> str:
    return dt.astimezone(datetime.UTC).strftime(constants.GCLOUD_DATE_FMT)


def is_saturday_pm_mass(date: datetime.datetime) -> bool:
    """Determines if the mass is the Saturday PM Mass at 5:30 PM"""
    return date.weekday() == models.Weekday.SATURDAY and (date.hour, date.minute) == constants.SATURDAY_EVENING_MASS


def to_saturday_mass(dt: datetime.datetime | datetime.date) -> datetime.datetime:
    """Converts the Sunday mass to the 5:30 PM Saturday mass"""
    assert dt is not None
    assert dt.weekday() == models.Weekday.SUNDAY
    saturday = dt - datetime.timedelta(days=1)
    return datetime.datetime(
        saturday.year,
        saturday.month,
        saturday.day,
        constants.SATURDAY_EVENING_MASS[0],
        constants.SATURDAY_EVENING_MASS[1],
        0,
        tzinfo=dateutil.tz.tzlocal(),
    )


def truncate(string: str, max_length: int = constants.MAX_FIELD_LEN) -> str:
    """
    Truncates the string to max_length.
    If the character at string[max_length] is not a space, it searches for the first preceding
    whitespace character and truncastes from there.
    """
    string = string.replace("\n", " ")
    if len(string) > max_length:
        idx = max_length
        for idx in range(max_length, 0, -1):
            if string[idx] == " ":
                break
        string = string[:max_length] if idx > 0 else string[:idx]

    return string


def add_months(dt: datetime.date, months_to_add: int) -> datetime.date:
    """Adds the number of monts to the specified datetime."""
    return datetime.date(
        dt.year + (dt.month + months_to_add - 1) // 12,
        (dt.month + months_to_add - 1) % 12 + 1,
        dt.day,
    )


def get_next_christmas_pageant() -> datetime.datetime:
    now = datetime.datetime.now(tz=constants.DEFAULT_TIMEZONE)
    year = now.year
    if now.month == constants.CHRISTMAS_PAGEANT_DATE[0] and now.day > constants.CHRISTMAS_PAGEANT_DATE[1]:
        year += 1

    return datetime.datetime(
        year,
        constants.CHRISTMAS_PAGEANT_DATE[0],
        constants.CHRISTMAS_PAGEANT_DATE[1],
        constants.CHRISTMAS_PAGEANT_TIME[0],
        constants.CHRISTMAS_PAGEANT_TIME[1],
        0,
        tzinfo=constants.DEFAULT_TIMEZONE,
    )
