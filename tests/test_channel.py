import datetime as dt
from collections.abc import Callable
from typing import Any, cast
from unittest.mock import Mock

from stjoseph.api import models
from stjoseph.api.services.channel import Channel


def test_upsert_broadcast_sends_recording_location_to_video_update() -> None:
    channel = Channel(creds=Mock())
    recorded_calls: list[tuple[str, dict[str, object]]] = []

    class FakeRequest:
        def __init__(self, response: dict[str, object]) -> None:
            self._response = response

        def execute(self) -> dict[str, object]:
            return self._response

    class FakeLiveBroadcasts:
        def update(self, part: str, body: dict[str, object]) -> FakeRequest:
            assert part == "snippet,status"
            return FakeRequest({"id": "video123"})

    class FakeVideos:
        def update(self, part: str, body: dict[str, object]) -> FakeRequest:
            recorded_calls.append((part, body))
            return FakeRequest({})

    class FakeResource:
        def liveBroadcasts(self) -> FakeLiveBroadcasts:  # noqa: N802
            return FakeLiveBroadcasts()

        def videos(self) -> FakeVideos:
            return FakeVideos()

    def execute_with_retry(request_factory: Callable[[Any], Any]) -> Any:  # noqa: ANN401
        return request_factory(FakeResource()).execute()

    object.__setattr__(channel, "_execute_with_retry", Mock(side_effect=execute_with_retry))

    video_id = channel.update_broadcast(
        "existing-id",
        "Test title",
        "Test description",
        dt.datetime.now(dt.UTC),
        scheduled_end_time=None,
        is_public=False,
        dry_run=False,
        recording_location=models.DEFAULT_LOCATION,
    )

    assert video_id == "video123"
    assert recorded_calls, "Expected videos.update to be called"
    part, body = recorded_calls[0]
    assert part == "snippet,recordingDetails"
    assert cast("dict[str, object]", body["recordingDetails"]) == {
        "locationDescription": models.DEFAULT_LOCATION.description,
        "location": {
            "latitude": models.DEFAULT_LOCATION.latitude,
            "longitude": models.DEFAULT_LOCATION.longitude,
            "altitude": models.DEFAULT_LOCATION.altitude,
        },
    }
    assert cast("dict[str, str]", cast("dict[str, object]", body["snippet"]))["title"] == "Test title"


def test_update_video_details_preserves_writable_snippet_fields() -> None:
    channel = Channel(creds=Mock())
    recorded_calls: list[tuple[str, dict[str, object]]] = []

    class FakeRequest:
        def __init__(self, response: dict[str, object]) -> None:
            self._response = response

        def execute(self) -> dict[str, object]:
            return self._response

    class FakeVideos:
        def list(self, part: str, id: str) -> FakeRequest:  # noqa: A002
            snippet = {"title": "Old", "description": "Old", "categoryId": "29", "channelId": "chan", "tags": ["mass"]}
            return FakeRequest({"items": [{"id": id, "snippet": snippet}]})

        def update(self, part: str, body: dict[str, object]) -> FakeRequest:
            recorded_calls.append((part, body))
            return FakeRequest({})

    class FakeResource:
        def videos(self) -> FakeVideos:
            return FakeVideos()

    def execute_with_retry(request_factory: Callable[[Any], Any]) -> Any:  # noqa: ANN401
        return request_factory(FakeResource()).execute()

    object.__setattr__(channel, "_execute_with_retry", Mock(side_effect=execute_with_retry))

    channel.update_video_details("video123", "New title", "New description")

    assert recorded_calls == [
        (
            "snippet",
            {
                "id": "video123",
                "snippet": {
                    "categoryId": "29",
                    "tags": ["mass"],
                    "title": "New title",
                    "description": "New description",
                },
            },
        )
    ]
