import datetime
from typing import Final

import jinja2
from catholic_mass_readings.models import Mass, SectionType

from stjoseph.api import constants

DESCRIPTION: Final[str] = """
Please consider giving this video a like, and subscribing to the channel. Thanks for watching, and see you all next week. Please share this video with family and friends.
{% if url %}
{{ url }}
{% endif -%}
{%- if text %}
{{- text }}
{% endif -%}
"""  # noqa: E501


def generate_description(mass: Mass) -> str:
    environment = jinja2.Environment(autoescape=True)
    template = environment.from_string(DESCRIPTION)
    text = template.render(text=_get_mass_text(mass), url=mass.url)
    if len(text) <= constants.MAX_DESCRIPTION_LENGTH:
        return text
    text = template.render(text=_get_short_mass_text(mass), url=mass.url)
    if len(text) <= constants.MAX_DESCRIPTION_LENGTH:
        return text
    text = template.render(text=_get_header_mass_text(mass), url=mass.url)
    if len(text) <= constants.MAX_DESCRIPTION_LENGTH:
        return text
    return template.render(url=mass.url)


def generate_title(mass_date: datetime.datetime) -> str:
    return f"Mass {mass_date:%B %d, %Y - %-I:%M %p}"


def _get_mass_text(mass: Mass) -> str:
    """Returns a formatted representation of the mass."""
    lines: list[str] = []
    for section in mass.sections:
        lines.extend("\n" + reading.format(section) for reading in section.readings[:1])

    return "\n".join(map(str, lines))


def _get_short_mass_text(mass: Mass) -> str:
    """
    Returns a formatted representation of the mass.
    Removes the contents from everything other than the Readings and Gospels.
    """
    lines: list[str] = []
    for section in mass.sections:
        if section.type_ in (SectionType.READING, SectionType.GOSPEL):
            lines.extend("\n" + reading.format(section) for reading in section.readings[:1])
        else:
            lines.extend("\n" + reading.format(section).splitlines()[0] for reading in section.readings[:1])

    return "\n".join(map(str, lines))


def _get_header_mass_text(mass: Mass) -> str:
    """Returns a formatted representation of the mass using only the header for each section."""
    lines: list[str] = []
    for section in mass.sections:
        if section.type_ in (SectionType.READING, SectionType.GOSPEL):
            lines.extend("\n" + "\n".join(reading.format(section).splitlines()[:2]) for reading in section.readings[:1])
        else:
            lines.extend("\n" + reading.format(section).splitlines()[0] for reading in section.readings[:1])

    return "\n".join(map(str, lines))
