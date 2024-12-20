from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Final, cast

import backoff
import google.auth.exceptions
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest, MediaFileUpload

from stjoseph.api import constants, models, resources, utils

if TYPE_CHECKING:
    from collections.abc import Iterable

    from stjoseph.api import oauth2


logger = logging.getLogger(__name__)


class Channel:
    SCOPES: Final[list[str]] = [
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    def __init__(self, creds: oauth2.CredentialsManager) -> None:
        self.creds = creds

    def get_channels(self) -> dict[str, Any]:
        youtube = self._create_resource()
        return youtube.channels().list(part="snippet", mine=True).execute()

    def broadcasts(self) -> Iterable[dict[str, Any]]:
        youtube = self._create_resource()
        return self._get_pages(
            youtube.liveBroadcasts(),
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
        youtube = self._create_resource()
        youtube.liveBroadcasts().delete(id=broadcast_id).execute()
        logger.info("Broadcast with ID %s has been deleted.", broadcast_id)

    def schedule_broadcast(
        self,
        title: str,
        description: str,
        scheduled_start_time: datetime.datetime,
        is_public: bool = False,
        dry_run: bool = False,
    ) -> str:
        privacy_status = "public" if is_public else "private"
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": utils.to_gcloude_datetime(scheduled_start_time),
                "scheduledEndTime": utils.to_gcloude_datetime(scheduled_start_time + datetime.timedelta(hours=1)),
            },
            "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": True},
        }

        logger.info("Scheduling mass%s", " [DRY-RUN]" if dry_run else "")
        logger.info("Date: %s", scheduled_start_time)
        logger.info("Title: %s", title)
        logger.info("Visibility: %s", privacy_status)
        logger.info("Description: %s", utils.truncate(description, constants.MAX_FIELD_LEN))

        if dry_run:
            return constants.NO_OP

        youtube = self._create_resource()
        broadcast_request = youtube.liveBroadcasts().insert(
            part="snippet,status",
            body=body,
        )

        broadcast_response = self._execute_with_retry(broadcast_request)

        broadcast_id = broadcast_response["id"]
        logger.info(
            "Successfully scheduled ID: %s, url: %s",
            broadcast_id,
            constants.LIVE_STREAMING_URL_FMT.format(VIDEO_ID=broadcast_id),
        )

        # Upload the thumbnail
        assert resources.THUMBNAIL.is_file()
        media = MediaFileUpload(resources.THUMBNAIL.as_posix(), mimetype=resources.THUMBNAIL_MIME_TYPE)
        thumbnail_request = youtube.thumbnails().set(videoId=broadcast_id, media_body=media)
        self._execute_with_retry(thumbnail_request)
        return broadcast_id

    def update_broadcast(  # noqa: PLR0913
        self,
        broadcast_id: str,
        title: str,
        description: str,
        scheduled_start_time: datetime.datetime,
        is_public: bool = False,
        dry_run: bool = False,
    ) -> str:
        privacy_status = "public" if is_public else "private"
        body = {
            "id": broadcast_id,
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": utils.to_gcloude_datetime(scheduled_start_time),
                "scheduledEndTime": utils.to_gcloude_datetime(scheduled_start_time + datetime.timedelta(hours=1)),
            },
            "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": True},
        }

        logger.info("Updating mass%s", " [DRY-RUN]" if dry_run else "")
        logger.info("Date: %s", scheduled_start_time)
        logger.info("Title: %s", title)
        logger.info("Visibility: %s", privacy_status)
        logger.info("Description: %s", utils.truncate(description, constants.MAX_FIELD_LEN))

        if dry_run:
            return constants.NO_OP

        youtube = self._create_resource()
        broadcast_request = youtube.liveBroadcasts().update(
            part="snippet,status",
            body=body,
        )

        broadcast_response = self._execute_with_retry(broadcast_request)

        broadcast_id = broadcast_response["id"]
        logger.info(
            "Successfully scheduled ID: %s, url: %s",
            broadcast_id,
            constants.LIVE_STREAMING_URL_FMT.format(VIDEO_ID=broadcast_id),
        )

        # Upload the thumbnail
        assert resources.THUMBNAIL.is_file()
        media = MediaFileUpload(resources.THUMBNAIL.as_posix(), mimetype=resources.THUMBNAIL_MIME_TYPE)
        thumbnail_request = youtube.thumbnails().set(videoId=broadcast_id, media_body=media)
        self._execute_with_retry(thumbnail_request)
        return broadcast_id

    @backoff.on_exception(backoff.expo, AttributeError, max_tries=constants.MAX_RETRY)
    def _create_resource(self) -> Resource:
        return build(
            "youtube", "v3", credentials=self.creds.create_oauth_credentials(self.SCOPES), cache_discovery=False
        )

    def _get_pages(self, resource: Resource, select_key: str, **kwargs: Any) -> Iterable[Any]:  # noqa: ANN401
        try:
            next_page_token: str | None = None
            start_idx = 0
            page_count = 1
            while True:
                request = cast(
                    HttpRequest,
                    resource.list(
                        pageToken=next_page_token,
                        **kwargs,
                    ),
                )

                results = self._execute_with_retry(request)
                values = cast(list[dict[str, Any]], results.get(select_key, []))

                total_len = start_idx + len(values)
                logger.debug("Page: %d (%d-%d %s)", page_count, start_idx, total_len, select_key)

                yield from values

                next_page_token = results.get("nextPageToken")
                if next_page_token is None:
                    break

                start_idx = total_len
                page_count += 1
        except google.auth.exceptions.RefreshError:
            logger.exception("Token failed to be refreshed", exc_info=False)
            self.creds.invalidate_token()
            raise

    @staticmethod
    @backoff.on_exception(backoff.expo, HttpError, max_tries=constants.MAX_RETRY)
    def _execute_with_retry(request: HttpRequest) -> dict[str, Any]:
        return request.execute()

    @staticmethod
    def _parse_datetime(date_string: str | None) -> datetime.datetime | None:
        return utils.parse_gcloud_datetime(date_string) if date_string is not None else None

    @staticmethod
    def _create_live_stream_from_item(item: dict[str, Any]) -> models.LiveStream:
        snippet = item["snippet"]
        scheduled_start = Channel._parse_datetime(snippet.get("scheduledStartTime"))
        return models.LiveStream(item["id"], snippet["title"], snippet["description"], scheduled_start)
