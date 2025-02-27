from __future__ import annotations

import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, Final

import asyncclick as click
from catholic_mass_readings import USCCB, models

from stjoseph.api import constants, generators, oauth2, services, utils
from stjoseph.commands.common import cli

if TYPE_CHECKING:
    from os import PathLike

    from catholic_mass_readings.models import Mass

logger = logging.getLogger(__name__)

_TODAY: Final[str] = USCCB.today().strftime(constants.DATE_FMT)
_TYPES: Final[list[str]] = [t.name for t in models.MassType]
_CHRISTMAS_PAGENT: Final[str] = utils.get_next_christmas_pageant().strftime(constants.DATE_TIME_FMT)


def _get_mass_types(ctx: click.Context, param: click.Option, value: tuple[str, ...]) -> list[models.MassType] | None:
    return list(map(models.MassType, value)) if value else None


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
def list_mass_schedules(credentials: PathLike, token: PathLike) -> None:
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
    "--dry-run",
    type=bool,
    is_flag=True,
    help="Flag indicating whether this is a dry-run",
)
def delete_duplicate_broadcasts(credentials: PathLike, token: PathLike, dry_run: bool) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    duplicate_broadcasts = channel_svc.get_duplicated_schedules_dates()
    if not duplicate_broadcasts:
        logger.info("No duplicate broadcasts found.")
        return

    for date, broadcast_ids in duplicate_broadcasts.items():
        logger.info(
            "Date: %s, has the following duplicated broadcast ids: %s",
            date.strftime("%B %d, %Y - %-I:%M %p"),
            sorted(broadcast_ids),
        )
        if dry_run is False:
            for broadcast_id in broadcast_ids:
                channel_svc.delete_broadcast(broadcast_id)


@cli.command()
@click.argument("date", type=click.DateTime([constants.DATE_TIME_FMT]))
@click.option(
    "-m",
    "--mass-date",
    type=click.DateTime([constants.DATE_FMT]),
    help="The date of the mass to use for the contents of the liturgy",
)
@click.option(
    "-e",
    "--schedule-end",
    type=click.DateTime([constants.DATE_TIME_FMT]),
    help="The time when the broadcast is complete",
)
@click.option(
    "-t",
    "--type",
    "types",
    type=click.Choice(_TYPES, case_sensitive=False),
    multiple=True,
    help="The mass type",
    callback=_get_mass_types,
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
@click.option(
    "--force",
    type=bool,
    is_flag=True,
    help="Flag indicating whether to overwrite even if the mass exists.",
)
@click.pass_context
async def schedule_mass(  # noqa: PLR0913
    ctx: click.Context,
    date: datetime.datetime,
    schedule_end: datetime.datetime | None,
    mass_date: datetime.datetime | None,
    types: list[models.MassType] | None,
    credentials: PathLike,
    token: PathLike,
    public: bool,
    dry_run: bool,
    force: bool,
) -> None:
    if mass_date is None:
        mass_date = date
        if utils.is_saturday_pm_mass(date):
            mass_date = date + datetime.timedelta(days=1)
            logger.info("Querying for mass on Sunday: %s", mass_date.date())

    if schedule_end is None:
        schedule_end = date + datetime.timedelta(hours=1)

    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    # Check if this mass is already scheduled:
    scheduled_dates = channel_svc.get_scheduled_dates()
    broadcast_id = scheduled_dates.get(date.astimezone(datetime.UTC))
    if broadcast_id is not None:
        if not force:
            logger.warning("%s is already scheduled under %s.", date, broadcast_id)
            return

        logger.info("%s is already scheduled under %s.", date, broadcast_id)

    # Query the mass readings:
    async with USCCB() as usccb:
        mass = await usccb.get_mass_from_date(mass_date.date(), types)

    if not mass:
        logger.error("Failed to find a mass on %s", mass_date)
        ctx.exit(1)
        return

    # Generate title/description and publish:
    title = generators.generate_title(date, mass.title)
    description = generators.generate_description(mass)
    if broadcast_id is None:
        channel_svc.schedule_broadcast(title, description, date, schedule_end, is_public=public, dry_run=dry_run)
    else:
        channel_svc.update_broadcast(
            broadcast_id, title, description, date, schedule_end, is_public=public, dry_run=dry_run
        )


@cli.command()
@click.option("-s", "--start", type=click.DateTime([constants.DATE_FMT]), default=_TODAY)
@click.option("-e", "--end", type=click.DateTime([constants.DATE_FMT]))
@click.option(
    "-t",
    "--type",
    "types",
    type=click.Choice(_TYPES, case_sensitive=False),
    multiple=True,
    help="The mass type",
    callback=_get_mass_types,
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
@click.option(
    "--force",
    type=bool,
    is_flag=True,
    help="Flag indicating whether to overwrite even if the mass exists.",
)
async def schedule_masses(  # noqa: PLR0913
    start: datetime.datetime,
    end: datetime.datetime | None,
    types: list[models.MassType] | None,
    credentials: PathLike,
    token: PathLike,
    public: bool,
    dry_run: bool,
    force: bool,
) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    start_date = start.date()
    end_date = None if end is None else end.date()

    # Check if this mass is already scheduled:
    scheduled_dates = channel_svc.get_scheduled_dates()

    # Query the mass readings:
    async with USCCB() as usccb:
        dates = list(usccb.get_sunday_mass_dates(start_date, end_date))
        # We schedule Sunday masses at 5:30 PM the Saturday before,
        # if running this on that Sunday, we want to skip dates
        # that have already passed.
        dates = [d for d in dates if utils.to_saturday_mass(d).date() >= USCCB.today()]
        if not force:
            # Filter out all dates that have already been scheduled:
            dates = [d for d in dates if utils.to_saturday_mass(d).astimezone(datetime.UTC) not in scheduled_dates]

        if not dates:
            logger.info("There are no new dates to schedule.")
            return

        logger.info("Querying for masses for the following dates: [%s]", ", ".join(list(map(str, dates))))
        masses: list[Mass] = []
        missing = 0
        tasks = [usccb.get_mass_from_date(dt, types) for dt in dates]
        responses = await asyncio.gather(*tasks)
        masses = [m for m in responses if m]
        missing = len(tasks) - len(masses)

    if missing:
        logger.warning("There are %d missing", missing)

    for mass in masses:
        # Generate title/description and publish:
        assert mass.date is not None
        date = utils.to_saturday_mass(mass.date)
        schedule_end = date + datetime.timedelta(hours=1)
        title = generators.generate_title(date, mass.title)
        description = generators.generate_description(mass)
        if force:
            broadcast_id = scheduled_dates.get(utils.to_saturday_mass(mass.date).astimezone(datetime.UTC))
            if broadcast_id is not None:
                channel_svc.update_broadcast(
                    broadcast_id, title, description, date, schedule_end, is_public=public, dry_run=dry_run
                )
                continue

        channel_svc.schedule_broadcast(title, description, date, schedule_end, is_public=public, dry_run=dry_run)


@cli.command()
@click.argument("date", type=click.DateTime([constants.DATE_TIME_FMT]), default=_CHRISTMAS_PAGENT)
@click.option(
    "-e",
    "--schedule-end",
    type=click.DateTime([constants.DATE_TIME_FMT]),
    help="The time when the broadcast is complete",
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
@click.option(
    "--force",
    type=bool,
    is_flag=True,
    help="Flag indicating whether to overwrite even if the mass exists.",
)
async def schedule_christmas_pageant(  # noqa: PLR0913
    date: datetime.datetime,
    schedule_end: datetime.datetime | None,
    credentials: PathLike,
    token: PathLike,
    public: bool,
    dry_run: bool,
    force: bool,
) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    if schedule_end is None:
        schedule_end = date + datetime.timedelta(minutes=30)
    else:
        schedule_end = schedule_end.astimezone(datetime.UTC)

    # Check if this is already scheduled:
    scheduled_dates = channel_svc.get_scheduled_dates()
    if date.date() < USCCB.today():
        logger.error("You cannot schedule in the past.")
        return

    broadcast_id = scheduled_dates.get(date.astimezone(datetime.UTC))
    if broadcast_id is not None:
        if force is False:
            logger.warning("%s is already scheduled under %s.", date, broadcast_id)
            return

        logger.info("%s is already scheduled under %s.", date, broadcast_id)

    title = generators.generate_christmas_pageant(date)
    description = generators.generate_description_christmas_pageant()
    if force:
        if broadcast_id is not None:
            channel_svc.update_broadcast(
                broadcast_id, title, description, date, schedule_end, is_public=public, dry_run=dry_run
            )
            return

    channel_svc.schedule_broadcast(title, description, date, schedule_end, is_public=public, dry_run=dry_run)
