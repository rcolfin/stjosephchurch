from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any, Final, cast

import backoff
import google.auth.exceptions
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest, MediaFileUpload

from stjoseph.api import constants, models, oauth2, resources, utils

if TYPE_CHECKING:
    import datetime
    from collections.abc import Callable, Iterable


logger = logging.getLogger(__name__)


class Channel:
    SCOPES: Final[list[str]] = [
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    def __init__(self, creds: oauth2.CredentialsManager) -> None:
        self.creds = creds

    def get_channels(self) -> dict[str, Any]:
        return self._execute_with_retry(lambda resource: resource.channels().list(part="snippet", mine=True))

    def broadcasts(self) -> Iterable[dict[str, Any]]:
        return self._get_pages(
            "items",
            part="id,snippet,status",
            broadcastStatus="upcoming",
            broadcastType="event",
        )

    def list_scheduled_livestreams(self) -> Iterable[models.LiveStream]:
        return map(self._create_live_stream_from_item, self.broadcasts())

    def get_scheduled_dates(self) -> dict[datetime.datetime, str]:
        """Gets a list of the upcoming scheduled dates to id."""
        return {x.scheduled_start: x.id for x in self.list_scheduled_livestreams() if x.scheduled_start is not None}

    def delete_broadcast(self, broadcast_id: str) -> None:
        self._execute_with_retry(lambda resource: resource.liveBroadcasts().delete(id=broadcast_id))
        logger.info("Broadcast with ID %s has been deleted.", broadcast_id)

    def schedule_broadcast(  # noqa: PLR0913
        self,
        title: str,
        description: str,
        scheduled_start_time: datetime.datetime,
        scheduled_end_time: datetime.datetime | None = None,
        is_public: bool = False,
        dry_run: bool = False,
    ) -> str:
        return self._upsert_broadcast(
            None,
            title,
            description,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            is_public=is_public,
            dry_run=dry_run,
        )

    def update_broadcast(  # noqa: PLR0913
        self,
        broadcast_id: str,
        title: str,
        description: str,
        scheduled_start_time: datetime.datetime,
        scheduled_end_time: datetime.datetime | None = None,
        is_public: bool = False,
        dry_run: bool = False,
    ) -> str:
        return self._upsert_broadcast(
            broadcast_id,
            title,
            description,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            is_public=is_public,
            dry_run=dry_run,
        )

    def _upsert_broadcast(  # noqa: PLR0913
        self,
        broadcast_id: str | None,
        title: str,
        description: str,
        scheduled_start_time: datetime.datetime,
        scheduled_end_time: datetime.datetime | None = None,
        is_public: bool = False,
        dry_run: bool = False,
    ) -> str:
        self._assert_description_len(description)
        privacy_status = "public" if is_public else "private"
        body: dict[str, Any] = {
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": utils.to_gcloude_datetime(scheduled_start_time),
            },
            "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": True},
        }

        if scheduled_end_time is not None:
            body["snippet"]["scheduledEndTime"] = utils.to_gcloude_datetime(scheduled_end_time)

        if broadcast_id is not None:
            body["id"] = broadcast_id
            logger.info("Updating mass%s", " [DRY-RUN]" if dry_run else "")

        else:
            logger.info("Scheduling mass%s", " [DRY-RUN]" if dry_run else "")

        logger.info("Start Time: %s", scheduled_start_time)
        if scheduled_end_time is not None:
            logger.info("Stop Time: %s", scheduled_end_time)

        logger.info("Title: %s", title)
        logger.info("Visibility: %s", privacy_status)
        logger.info("Description: %s", utils.truncate(description, constants.MAX_FIELD_LEN))

        if dry_run:
            return constants.NO_OP

        broadcast_response = self._execute_with_retry(
            lambda resource: resource.liveBroadcasts().insert(
                part="snippet,status",
                body=body,
            )
        )

        broadcast_id = cast(str, broadcast_response["id"])
        logger.info(
            "Successfully scheduled ID: %s, url: %s",
            broadcast_id,
            constants.LIVE_STREAMING_URL_FMT.format(VIDEO_ID=broadcast_id),
        )

        # Upload the thumbnail
        assert resources.THUMBNAIL.is_file()
        media = MediaFileUpload(resources.THUMBNAIL.as_posix(), mimetype=resources.THUMBNAIL_MIME_TYPE)
        self._execute_with_retry(lambda resource: resource.thumbnails().set(videoId=broadcast_id, media_body=media))
        return broadcast_id

    @cached_property
    @backoff.on_exception(backoff.expo, AttributeError, max_tries=constants.MAX_RETRY)
    def _resource(self) -> Resource:
        credentials = self.creds.create_oauth_credentials(self.SCOPES)
        return build("youtube", "v3", credentials=credentials, cache_discovery=False)

    def _reset_resource(self) -> None:
        logger.info("Resetting resource.")
        self.__dict__.pop("_resource", None)

    def _get_pages(self, select_key: str, **kwargs: Any) -> Iterable[Any]:  # noqa: ANN401
        next_page_token: str | None = None
        start_idx = 0
        page_count = 1
        while True:

            def get_request(resource: Resource, next_page_token: str | None = next_page_token) -> HttpRequest:
                return cast(
                    HttpRequest,
                    resource.liveBroadcasts().list(
                        pageToken=next_page_token,
                        **kwargs,
                    ),
                )

            results = self._execute_with_retry(get_request)
            values = cast(list[dict[str, Any]], results.get(select_key, []))

            total_len = start_idx + len(values)
            logger.debug("Page: %d (%d-%d %s)", page_count, start_idx, total_len, select_key)

            yield from values

            next_page_token = results.get("nextPageToken")
            if next_page_token is None:
                break

            start_idx = total_len
            page_count += 1

    @backoff.on_exception(backoff.expo, (google.auth.exceptions.RefreshError, HttpError), max_tries=constants.MAX_RETRY)
    def _execute_with_retry(self, request_factory: Callable[[Resource], HttpRequest]) -> dict[str, Any]:
        try:
            return request_factory(self._resource).execute()
        except google.auth.exceptions.RefreshError:
            logger.exception("Token failed to be refreshed", exc_info=False)
            self._reset_resource()
            raise

    @staticmethod
    def _parse_datetime(date_string: str | None) -> datetime.datetime | None:
        return utils.parse_gcloud_datetime(date_string) if date_string is not None else None

    @staticmethod
    def _create_live_stream_from_item(item: dict[str, Any]) -> models.LiveStream:
        snippet = item["snippet"]
        scheduled_start = Channel._parse_datetime(snippet.get("scheduledStartTime"))
        return models.LiveStream(item["id"], snippet["title"], snippet["description"], scheduled_start)

    @staticmethod
    def _assert_description_len(description: str) -> None:
        if len(description) > constants.MAX_DESCRIPTION_LENGTH:
            msg = f"Description is larger than {constants.MAX_DESCRIPTION_LENGTH}"
            raise ValueError(msg)
