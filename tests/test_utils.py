import datetime as dt

from stjoseph.api import constants, utils


def test_to_saturday_mass_uses_default_timezone() -> None:
    mass = utils.to_saturday_mass(dt.date(2026, 10, 25))
    assert mass.tzinfo is constants.DEFAULT_TIMEZONE
    assert mass.astimezone(dt.UTC) == dt.datetime(2026, 10, 24, 21, 30, tzinfo=dt.UTC)


def test_to_saturday_mass_standard_time() -> None:
    mass = utils.to_saturday_mass(dt.date(2026, 12, 6))
    assert mass.astimezone(dt.UTC) == dt.datetime(2026, 12, 5, 22, 30, tzinfo=dt.UTC)


def test_get_next_christmas_pageant_offset() -> None:
    pageant = utils.get_next_christmas_pageant()
    assert pageant.utcoffset() == dt.timedelta(hours=-5)
    assert (pageant.astimezone(dt.UTC).hour, pageant.astimezone(dt.UTC).minute) == (21, 0)
