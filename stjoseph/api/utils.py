from __future__ import annotations

import datetime

from stjoseph.api import constants, models


def parse_gcloud_datetime(date_string: str) -> datetime.datetime:
    """Parses a Google Cloud API Date String"""
    return datetime.datetime.strptime(date_string, constants.GCLOUD_DATE_FMT).replace(tzinfo=datetime.UTC)


def to_gcloude_datetime(dt: datetime.datetime) -> str:
    return dt.astimezone(datetime.UTC).strftime(constants.GCLOUD_DATE_FMT)


def is_saturday_pm_mass(date: datetime.datetime) -> bool:
    """Determines if the mass is the Saturday PM Mass at 5:30 PM"""
    return date.weekday() == models.Weekday.SATURDAY and (date.hour, date.minute) == constants.SATURDAY_EVENING_MASS


def to_saturday_mass(dt: datetime.datetime | datetime.date) -> datetime.datetime:
    """Converts the Sunday mass to the 5:30 PM Saturday mass"""
    assert dt is not None
    assert dt.weekday() == models.Weekday.SUNDAY
    saturday = dt - datetime.timedelta(days=1)
    return datetime.datetime(  # noqa: DTZ001
        saturday.year,
        saturday.month,
        saturday.day,
        constants.SATURDAY_EVENING_MASS[0],
        constants.SATURDAY_EVENING_MASS[1],
        0,
    )
