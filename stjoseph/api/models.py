from __future__ import annotations

import datetime
from enum import Enum, IntEnum, unique
from typing import NamedTuple

from catholic_mass_readings import USCCB

from stjoseph.api import constants, utils


class LiveStream(NamedTuple):
    id: str
    title: str
    description: str
    published_at: datetime.datetime | None
    scheduled_start: datetime.datetime | None
    actual_start: datetime.datetime | None
    actual_end: datetime.datetime | None

    def __repr__(self) -> str:
        description = utils.truncate(self.description, constants.MAX_FIELD_LEN)
        result = f"id='{self.id}' title='{self.title}' description='{description}' scheduled='{self.scheduled_start}'"
        if self.published_at:
            result += f", published_at='{self.published_at}"

        if self.actual_start and self.actual_end:
            result += f", actual_start='{self.actual_start}, actual_end='{self.actual_end}, duration='{self.duration}'"
        return result

    def __str__(self) -> str:
        return repr(self)

    @property
    def duration(self) -> datetime.timedelta | None:
        """Gets the actual duration of the mass"""
        return self.actual_end - self.actual_start if self.actual_start and self.actual_end else None

    def is_eligible_for_deletion(self) -> bool:
        if self.scheduled_start and self.scheduled_start.date() >= USCCB.today():
            return False  # starting in the future.

        return (
            not self.published_at
            or self.duration is None
            or self.duration.total_seconds() < datetime.timedelta(minutes=15).total_seconds()
        )


@unique
class Weekday(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@unique
class BroadcastStatus(str, Enum):
    ACTIVE = "active"
    ALL = "all"
    COMPLETED = "completed"
    UPCOMING = "upcoming"


@unique
class BroadcastType(str, Enum):
    ALL = "all"
    EVENT = "event"
    PERSISTENT = "persistent"


@unique
class VideoCategory(IntEnum):
    FILM_AND_ANIMATION = 1
    AUTOS_AND_VEHICLES = 2
    MUSIC = 10
    PETS_AND_ANIMALS = 15
    SPORTS = 17
    TRAVEL_AND_EVENTS = 19
    GAMING = 20
    PEOPLE_AND_BLOGS = 22
    COMEDY = 23
    ENTERTAINMENT = 24
    NEWS_AND_POLITICS = 25
    HOWTO_AND_STYLE = 26
    EDUCATION = 27
    SCIENCE_AND_TECHNOLOGY = 28
    NONPROFITS_AND_ACTIVISM = 29
    MOVIES = 30
    ANIME_AND_ANIMATION = 31
    ACTION_AND_ADVENTURE = 32
    CLASSICS = 33
    DOCUMENTARY = 35
    DRAMA = 36
    FAMILY = 37
    FOREIGN = 38
    HORROR = 39
    SCI_FI_AND_FANTASY = 40
    THRILLERS = 41
    SHORTS = 42
    SHOWS = 43
    TRAILERS = 44
