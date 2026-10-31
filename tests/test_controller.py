
from threading import Event
from unittest.mock import Mock

import pytest

from ytvlc.controller import PlaybackController
from ytvlc.extractor import Playlist, PlaylistEntry


@pytest.fixture
def playlist():
    entries = [
        PlaylistEntry(
            video_id="video_1",
            title="First track",
            index=1,
            url="https://www.youtube.com/watch?v=video_1",
        ),
        PlaylistEntry(
            video_id="video_2",
            title="Second track",
            index=2,
            url="https://www.youtube.com/watch?v=video_2",
        ),
    ]

    return Playlist(
        title="Test playlist",
        playlist_id="test_playlist",
        entries=entries,
        unavailable_count=0,
    )


@pytest.fixture
def dependencies():
    return {
        "instance": Mock(),
        "player": Mock(),
        "event_manager": Mock(),
        "resolver": Mock(
            side_effect=[
                "https://example.com/stream1.mp4",
                "https://example.com/stream2.mp4",
            ]
        ),
    }


def test_controller_resolves_and_starts_first_track(
    playlist,
    dependencies,
):
    controller = PlaybackController(
        playlist,
        instance=dependencies["instance"],
        player=dependencies["player"],
        resolver=dependencies["resolver"],
    )

    controller.start_track(playlist.entries[0])

    dependencies["resolver"].assert_called_once_with(
        playlist.entries[0]
    )
    dependencies["instance"].media_new.assert_called_once_with(
        "https://example.com/stream1.mp4"
    )
    dependencies["player"].set_media.assert_called_once()
    dependencies["player"].play.assert_called_once()


def test_end_event_signals_track_completion(
    playlist,
    dependencies,
):
    controller = PlaybackController(
        playlist,
        instance=dependencies["instance"],
        player=dependencies["player"],
        resolver=dependencies["resolver"],
    )

    controller.on_track_end(None)

    assert controller.track_finished.is_set()


def test_error_event_signals_playback_failure(
    playlist,
    dependencies,
):
    controller = PlaybackController(
        playlist,
        instance=dependencies["instance"],
        player=dependencies["player"],
        resolver=dependencies["resolver"],
    )

    controller.on_playback_error(None)

    assert controller.playback_failed.is_set()


def test_controller_stops_and_releases_resources(
    playlist,
    dependencies,
):
    controller = PlaybackController(
        playlist,
        instance=dependencies["instance"],
        player=dependencies["player"],
        resolver=dependencies["resolver"],
    )

    controller.cleanup()

    dependencies["player"].stop.assert_called_once()
    dependencies["player"].release.assert_called_once()
    dependencies["instance"].release.assert_called_once()
