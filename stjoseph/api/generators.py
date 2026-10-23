import datetime as dt
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


_ENV: Final[jinja2.Environment] = jinja2.Environment(autoescape=False)  # noqa: S701
_DESCRIPTION_TMPL: Final[jinja2.Template] = _ENV.from_string(DESCRIPTION)


def generate_description_christmas_pageant() -> str:
    return _DESCRIPTION_TMPL.render()


def generate_description(mass: Mass) -> str:
    for text_fn in (_get_mass_text, _get_short_mass_text, _get_header_mass_text):
        text = _DESCRIPTION_TMPL.render(text=text_fn(mass), url=mass.url)
        if len(text) <= constants.MAX_DESCRIPTION_LENGTH:
            return text
    return _DESCRIPTION_TMPL.render(url=mass.url)


def generate_christmas_pageant(mass_date: dt.datetime) -> str:
    return f"Chrismas Pageant {mass_date:%B %-d, %Y - %-I:%M %p}"


def generate_title(mass_date: dt.datetime, title: str) -> str:
    return f"Mass {mass_date:%B %-d, %Y - %-I:%M %p}: {title}"


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
