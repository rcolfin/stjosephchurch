from __future__ import annotations

from collections.abc import Iterable
from enum import Enum, EnumMeta, IntEnum
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from stjoseph.api import constants

if TYPE_CHECKING:
    import datetime


class _CaseInsensitiveEnumMeta(EnumMeta):
    def __call__(cls, value: str, *args: list[Any], **kwargs: Any) -> type[Enum]:  # noqa: ANN401
        try:
            return super().__call__(value, *args, **kwargs)
        except ValueError:
            items = cast(Iterable[Enum], cls)
            for item in items:
                if item.name.casefold() == value.casefold():
                    return cast(type[Enum], item)
            raise


class LiveStream(NamedTuple):
    id: str
    title: str
    description: str
    scheduled_start: datetime.datetime | None

    def __repr__(self) -> str:
        description = self.description.replace("\n", " ")
        if len(description) > constants.MAX_FIELD_LEN:
            idx = description.rfind(" ", 0, constants.MAX_FIELD_LEN)
            description = description[: constants.MAX_FIELD_LEN] if idx == -1 else description[:idx]

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
