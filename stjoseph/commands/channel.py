from __future__ import annotations

import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, Final

import asyncclick as click
from catholic_mass_readings import USCCB

from stjoseph.api import constants, generators, oauth2, services, utils
from stjoseph.commands.common import cli

if TYPE_CHECKING:
    from os import PathLike

    from catholic_mass_readings.models import Mass

logger = logging.getLogger(__name__)

_TODAY: Final[str] = USCCB.today().strftime(constants.DATE_TIME_FMT)
_MONTH_LATER: Final[str] = (USCCB.today() + datetime.timedelta(weeks=4)).strftime(constants.DATE_TIME_FMT)


@cli.command()
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
    "-t",
    "--token",
    type=click.Path(exists=False, dir_okay=False),
    default=constants.TOKEN_FILE,
    help="The path to the token file",
)
def list_schedule_masss(credentials: PathLike, token: PathLike) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    streams = channel_svc.list_scheduled_livestreams()
    for stream in streams:
        print(stream)  # noqa: T201


@cli.command()
@click.argument(
    "broadcast_id",
    type=str,
)
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
    "-t",
    "--token",
    type=click.Path(exists=False, dir_okay=False),
    default=constants.TOKEN_FILE,
    help="The path to the token file",
)
def delete_broadcast(broadcast_id: str, credentials: PathLike, token: PathLike) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    channel_svc.delete_broadcast(broadcast_id)


@cli.command()
@click.argument("date", type=click.DateTime([constants.DATE_TIME_FMT]))
@click.option(
    "-m",
    "--mass-date",
    type=click.DateTime([constants.DATE_TIME_FMT]),
    help="The date of the mass to use for the contents of the liturgy",
)
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
    "-t",
    "--token",
    type=click.Path(exists=False, dir_okay=False),
    default=constants.TOKEN_FILE,
    help="The path to the token file",
)
@click.option(
    "--public",
    type=bool,
    is_flag=True,
    help="Flag indicating whether this is a public video",
)
@click.option(
    "--dry-run",
    type=bool,
    is_flag=True,
    help="Flag indicating whether this is a dry-run",
)
@click.pass_context
async def schedule_mass(  # noqa: PLR0913
    ctx: click.Context,
    date: datetime.datetime,
    mass_date: datetime.datetime | None,
    credentials: PathLike,
    token: PathLike,
    public: bool,
    dry_run: bool,
) -> None:
    if mass_date is None:
        mass_date = date
        if utils.is_saturday_pm_mass(date):
            mass_date = date + datetime.timedelta(days=1)
            logger.info("Querying for mass on Sunday: %s", mass_date.date())

    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    # Check if this mass is already scheduled:
    scheduled_dates = channel_svc.get_scheduled_dates()
    if date.astimezone(datetime.UTC) in scheduled_dates:
        logger.warning("%s is already scheduled.", date)
        return

    # Query the mass readings:
    async with USCCB() as usccb:
        mass = await usccb.get_mass_from_date(mass_date.date())

    if not mass:
        logger.error("Failed to find a mass on %s", mass_date)
        ctx.exit(1)
        return

    # Generate title/description and publish:
    title = generators.generate_title(date)
    description = generators.generate_description(mass)
    channel_svc.schedule_broadcast(title, description, date, is_public=public, dry_run=dry_run)


@cli.command()
@click.option("-s", "--start", type=click.DateTime([constants.DATE_TIME_FMT]), default=_TODAY)
@click.option("-e", "--end", type=click.DateTime([constants.DATE_TIME_FMT]), default=_MONTH_LATER)
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
    "-t",
    "--token",
    type=click.Path(exists=False, dir_okay=False),
    default=constants.TOKEN_FILE,
    help="The path to the token file",
)
@click.option(
    "--public",
    type=bool,
    is_flag=True,
    help="Flag indicating whether this is a public video",
)
@click.option(
    "--dry-run",
    type=bool,
    is_flag=True,
    help="Flag indicating whether this is a dry-run",
)
async def schedule_masses(  # noqa: PLR0913
    start: datetime.datetime | None,
    end: datetime.datetime | None,
    credentials: PathLike,
    token: PathLike,
    public: bool,
    dry_run: bool,
) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    # Check if this mass is already scheduled:
    scheduled_dates = channel_svc.get_scheduled_dates()

    # Query the mass readings:
    async with USCCB() as usccb:
        start_date = start.date() if start else USCCB.today()
        end_date = end.date() if end else None
        dates = usccb.get_sunday_mass_dates(start_date, end_date)
        dates = [d for d in dates if utils.to_saturday_mass(d).astimezone(datetime.UTC) not in scheduled_dates]
        if not dates:
            logger.info("There are no new dates to schedule.")
            return

        logger.info("Querying for mass for %s", list(map(str, dates)))
        masses: list[Mass] = []
        missing = 0
        for task in asyncio.as_completed([usccb.get_mass_from_date(dt) for dt in dates]):
            mass = await task
            if mass is not None:
                masses.append(mass)
            else:
                missing += 1

    if missing:
        logger.warning("There are %d missing", missing)

    for mass in masses:
        # Generate title/description and publish:
        assert mass.date is not None
        date = utils.to_saturday_mass(mass.date)
        title = generators.generate_title(date)
        description = generators.generate_description(mass)
        channel_svc.schedule_broadcast(title, description, date, is_public=public, dry_run=dry_run)