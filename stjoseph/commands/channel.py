from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import TYPE_CHECKING, Final

import asyncclick as click
from catholic_mass_readings import USCCB, models

from stjoseph.api import constants, generators, oauth2, services, utils
from stjoseph.api import models as api_models
from stjoseph.commands.common import cli

if TYPE_CHECKING:
    from os import PathLike

logger = logging.getLogger(__name__)

_TODAY: Final[str] = USCCB.today().strftime(constants.DATE_FMT)
_TYPES: Final[list[str]] = [t.name for t in models.MassType]
_BROADCAST_STATUS: Final[list[str]] = [t.value for t in api_models.BroadcastStatus]
_BROADCAST_TYPES: Final[list[str]] = [t.value for t in api_models.BroadcastType]
_CHRISTMAS_PAGENT: Final[str] = utils.get_next_christmas_pageant().strftime(constants.DATE_TIME_FMT)


def _get_mass_date(date: dt.datetime) -> dt.datetime:
    """Gets the date of the mass whose readings are used for a broadcast on the specified date."""
    if utils.is_saturday_pm_mass(date):
        mass_date = date + dt.timedelta(days=1)
        logger.info("Querying for mass on Sunday: %s", mass_date.date())
        return mass_date
    return date


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
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
    "--token",
    type=click.Path(exists=False, dir_okay=False),
    default=constants.TOKEN_FILE,
    help="The path to the token file",
)
def list_past_mass_schedules(credentials: PathLike, token: PathLike) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    streams = channel_svc.list_completed_livestreams()
    for stream in streams:
        print(stream)  # noqa: T201


@cli.command()
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
    "--token",
    type=click.Path(exists=False, dir_okay=False),
    default=constants.TOKEN_FILE,
    help="The path to the token file",
)
def list_eligible_for_deletion(credentials: PathLike, token: PathLike) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    streams = channel_svc.list_eligible_for_deletion()
    any_eligible_for_deletion = False
    for stream in streams:
        any_eligible_for_deletion = True
        print(stream)  # noqa: T201
    if not any_eligible_for_deletion:
        logger.info("No eligible broadcasts found.")
        return


@cli.command()
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
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
def delete_eligible(credentials: PathLike, token: PathLike, dry_run: bool) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    streams = channel_svc.list_eligible_for_deletion()
    any_eligible_for_deletion = False
    for stream in streams:
        any_eligible_for_deletion = True
        if dry_run is False:
            channel_svc.delete_broadcast(stream.id)
        else:
            print(stream)  # noqa: T201
    if not any_eligible_for_deletion:
        logger.info("No eligible broadcasts found.")
        return


@cli.command()
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
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
@click.option(
    "--force",
    type=bool,
    is_flag=True,
    help="Flag indicating whether to skip the confirmation prompt.",
)
def delete_stale_schedules(credentials: PathLike, token: PathLike, dry_run: bool, force: bool) -> None:
    """Deletes scheduled masses for past dates that never went live, prompting for each unless --force."""
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    any_stale = False
    for stream in channel_svc.list_stale_livestreams():
        any_stale = True
        print(stream)  # noqa: T201
        if dry_run:
            continue
        if force or click.confirm(f"Delete broadcast {stream.id}?"):
            channel_svc.delete_broadcast(stream.id)
    if not any_stale:
        logger.info("No stale scheduled broadcasts found.")


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

    for date, broadcast in duplicate_broadcasts.items():
        logger.info(
            "Date: %s, has the following duplicated broadcast ids: %s",
            date.strftime("%B %d, %Y - %-I:%M %p"),
            sorted(broadcast),
        )
        if dry_run is False:
            for broadcast_id in broadcast:
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
    *,
    date: dt.datetime,
    schedule_end: dt.datetime | None,
    mass_date: dt.datetime | None,
    types: list[models.MassType] | None,
    credentials: PathLike,
    token: PathLike,
    public: bool,
    dry_run: bool,
    force: bool,
) -> None:
    if mass_date is None:
        mass_date = _get_mass_date(date)

    if schedule_end is None:
        schedule_end = date + dt.timedelta(hours=1)

    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    # Check if this mass is already scheduled:
    scheduled_dates = channel_svc.get_scheduled_dates()
    broadcast_id = scheduled_dates.get(date.astimezone(dt.UTC))
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
        await ctx.aexit(1)
        return

    # Generate title/description and publish:
    title = generators.generate_title(date, mass.title)
    description = generators.generate_description(mass)
    if broadcast_id is None:
        channel_svc.schedule_broadcast(title, description, date, schedule_end, is_public=public, dry_run=dry_run)
    else:
        channel_svc.update_broadcast(
            broadcast_id, title, description, date, scheduled_end_time=schedule_end, is_public=public, dry_run=dry_run
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
    start: dt.datetime,
    *,
    end: dt.datetime | None,
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

    # Compute dates before opening the browser — get_sunday_mass_dates is pure date math.
    dates = list(USCCB.get_sunday_mass_dates(start_date, end_date))
    # We schedule Sunday masses at 5:30 PM the Saturday before,
    # if running this on that Sunday, we want to skip dates
    # that have already passed.
    dates = [d for d in dates if utils.to_saturday_mass(d).date() >= USCCB.today()]
    if not force:
        # Filter out all dates that have already been scheduled:
        dates = [d for d in dates if utils.to_saturday_mass(d).astimezone(dt.UTC) not in scheduled_dates]

    if not dates:
        logger.info("There are no new dates to schedule.")
        return

    # Query the mass readings:
    logger.info("Querying for masses for the following dates: [%s]", ", ".join(map(str, dates)))
    async with USCCB() as usccb:
        tasks = [usccb.get_mass_from_date(d, types) for d in dates]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    masses = [m for m in responses if isinstance(m, models.Mass)]
    missing = len(tasks) - len(masses)

    if missing:
        logger.warning("There are %d missing", missing)

    for mass in masses:
        # Generate title/description and publish:
        if mass.date is None:
            logger.warning("Skipping mass with no date: %s", mass.title)
            continue
        date = utils.to_saturday_mass(mass.date)
        schedule_end = date + dt.timedelta(hours=1)
        title = generators.generate_title(date, mass.title)
        description = generators.generate_description(mass)
        if force:
            broadcast_id = scheduled_dates.get(utils.to_saturday_mass(mass.date).astimezone(dt.UTC))
            if broadcast_id is not None:
                channel_svc.update_broadcast(
                    broadcast_id,
                    title,
                    description,
                    date,
                    scheduled_end_time=schedule_end,
                    is_public=public,
                    dry_run=dry_run,
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
    date: dt.datetime,
    *,
    schedule_end: dt.datetime | None,
    credentials: PathLike,
    token: PathLike,
    public: bool,
    dry_run: bool,
    force: bool,
) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    schedule_end = date + dt.timedelta(minutes=30) if schedule_end is None else schedule_end.astimezone(dt.UTC)

    # Check if this is already scheduled:
    scheduled_dates = channel_svc.get_scheduled_dates()
    if date.date() < USCCB.today():
        logger.error("You cannot schedule in the past.")
        return

    broadcast_id = scheduled_dates.get(date.astimezone(dt.UTC))
    if broadcast_id is not None:
        if force is False:
            logger.warning("%s is already scheduled under %s.", date, broadcast_id)
            return

        logger.info("%s is already scheduled under %s.", date, broadcast_id)

    title = generators.generate_christmas_pageant(date)
    description = generators.generate_description_christmas_pageant()
    if force and broadcast_id is not None:
        channel_svc.update_broadcast(
            broadcast_id, title, description, date, scheduled_end_time=schedule_end, is_public=public, dry_run=dry_run
        )

        return

    channel_svc.schedule_broadcast(title, description, date, schedule_end, is_public=public, dry_run=dry_run)


@cli.command()
@click.option(
    "-c",
    "--credentials",
    type=click.Path(exists=True, dir_okay=False),
    default=constants.CREDENTIALS_FILE,
    help="The path to the credentials file",
)
@click.option(
    "--token",
    type=click.Path(exists=False, dir_okay=False),
    default=constants.TOKEN_FILE,
    help="The path to the token file",
)
@click.option(
    "-s",
    "--status",
    "broadcast_status",
    type=click.Choice(_BROADCAST_STATUS, case_sensitive=False),
    help="The broadcast status type",
    default=str(api_models.BroadcastStatus.ALL),
)
@click.option(
    "-t",
    "--type",
    "broadcast_type",
    type=click.Choice(_BROADCAST_TYPES, case_sensitive=False),
    help="The broadcast type",
    default=str(api_models.BroadcastType.ALL),
)
def broadcasts(
    credentials: PathLike,
    token: PathLike,
    broadcast_status: api_models.BroadcastStatus,
    broadcast_type: api_models.BroadcastType,
) -> None:
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)
    broadcasts = channel_svc.broadcasts(
        api_models.BroadcastStatus(broadcast_status.lower()), api_models.BroadcastType(broadcast_type.lower())
    )
    if not broadcasts:
        logger.info("No broadcasts found.")
        return

    for broadcast in broadcasts:
        print(broadcast)  # noqa: T201


@cli.command()
@click.argument("broadcast_id", type=str, required=False)
@click.option(
    "-d",
    "--date",
    type=click.DateTime([constants.DATE_TIME_FMT]),
    help="The date/time the broadcast actually aired (defaults to the scheduled time on the date it went live)",
)
@click.option(
    "-m",
    "--mass-date",
    type=click.DateTime([constants.DATE_FMT]),
    help="The date of the mass to use for the contents of the liturgy",
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
@click.option(
    "--force",
    type=bool,
    is_flag=True,
    help="Flag indicating whether to skip the confirmation prompt.",
)
@click.pass_context
async def correct_mass_dates(  # noqa: PLR0913
    ctx: click.Context,
    *,
    broadcast_id: str | None,
    date: dt.datetime | None,
    mass_date: dt.datetime | None,
    types: list[models.MassType] | None,
    credentials: PathLike,
    token: PathLike,
    dry_run: bool,
    force: bool,
) -> None:
    """
    Corrects the title and description of masses that went live using a broadcast scheduled for another date.
    Without a BROADCAST_ID, all completed broadcasts that aired on a different date than scheduled are corrected.
    Prompts before each correction unless --force.
    """
    creds = oauth2.CredentialsManager(credentials, token)
    channel_svc = services.Channel(creds)

    if broadcast_id is None:
        if date is not None or mass_date is not None:
            logger.error("--date and --mass-date require a BROADCAST_ID")
            await ctx.aexit(1)
            return
        streams = list(channel_svc.list_misdated_livestreams())
    else:
        stream = channel_svc.get_livestream(broadcast_id)
        if stream is None:
            logger.error("Broadcast %s was not found", broadcast_id)
            await ctx.aexit(1)
            return
        streams = [stream]

    if not streams:
        logger.info("No misdated broadcasts found.")
        return

    async with USCCB() as usccb:
        for stream in streams:
            aired = date or stream.get_aired_start()
            if aired is None:
                logger.warning("%s aired on its scheduled date; specify --date to correct it.", stream.id)
                continue

            try:
                mass = await usccb.get_mass_from_date((mass_date or _get_mass_date(aired)).date(), types)
            except Exception:
                logger.exception("Failed to query the mass for %s aired on %s", stream.id, aired)
                continue
            if not mass:
                logger.error("Failed to find a mass for %s aired on %s", stream.id, aired)
                continue

            title = generators.generate_title(aired, mass.title)
            description = generators.generate_description(mass)
            logger.info("Correcting %s: '%s' -> '%s'", stream.id, stream.title, title)
            if dry_run or force or click.confirm(f"Update {stream.id} to '{title}'?"):
                channel_svc.update_video_details(stream.id, title, description, dry_run=dry_run)
