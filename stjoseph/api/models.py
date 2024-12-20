from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, NamedTuple

from stjoseph.api import constants, utils

if TYPE_CHECKING:
    import datetime


class LiveStream(NamedTuple):
    id: str
    title: str
    description: str
    scheduled_start: datetime.datetime | None

    def __repr__(self) -> str:
        description = utils.truncate(self.description, constants.MAX_FIELD_LEN)
        return f"id='{self.id}' title='{self.title}' description='{description}' scheduled='{self.scheduled_start}'"

    def __str__(self) -> str:
        return repr(self)


class Weekday(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
