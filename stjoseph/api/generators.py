import datetime
from typing import Final

import jinja2
from catholic_mass_readings.models import Mass

DESCRIPTION: Final[str] = """
Please consider giving this video a like and subscribing to the channel. Thanks for watching and see you all next week. Please share this video with family and friends.

{{ text }}
"""  # noqa: E501


def generate_description(mass: Mass) -> str:
    environment = jinja2.Environment(autoescape=True)
    template = environment.from_string(DESCRIPTION)
    return template.render(text=_get_mass_text(mass))


def generate_title(mass_date: datetime.datetime) -> str:
    return f"Mass {mass_date:%B %d, %Y - %-I:%M %p}"


def _get_mass_text(mass: Mass) -> str:
    """Returns a formatted representation of the mass."""
    lines: list[str] = []
    for section in mass.sections:
        lines.extend(f"\n{section.header}: {reading}\n\n{reading.text}" for reading in section.readings[:1])

    return "\n".join(map(str, lines))
