
from threading import Event
from unittest.mock import Mock

import pytest

from ytvlc.controller import PlaybackController
from ytvlc.extractor import Playlist, PlaylistEntry
from ytvlc.resolver import StreamResolutionError

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



def test_run_advances_after_track_finishes(
    playlist,
    dependencies,
):
    controller = PlaybackController(
        playlist,
        instance=dependencies["instance"],
        player=dependencies["player"],
        resolver=dependencies["resolver"],
    )

    def finish_track(entry):
        controller.on_track_end(None)

    controller.start_track = Mock(side_effect=finish_track)

    controller.run()

    assert controller.start_track.call_args_list == [
        ((playlist.entries[0],),),
        ((playlist.entries[1],),),
    ]

    dependencies["player"].stop.assert_called_once()
    dependencies["player"].release.assert_called_once()
    dependencies["instance"].release.assert_called_once()


def test_run_skips_track_when_stream_resolution_fails(
    playlist,
    dependencies,
):
    controller = PlaybackController(
        playlist,
        instance=dependencies["instance"],
        player=dependencies["player"],
        resolver=dependencies["resolver"],
    )

    def start_track(entry):
        if entry == playlist.entries[0]:
            raise StreamResolutionError("Stream unavailable.")

        controller.on_track_end(None)

    controller.start_track = Mock(side_effect=start_track)

    controller.run()

    assert controller.start_track.call_args_list == [
        ((playlist.entries[0],),),
        ((playlist.entries[1],),),
    ]


def test_run_skips_track_when_vlc_reports_playback_error(
    playlist,
    dependencies,
):
    controller = PlaybackController(
        playlist,
        instance=dependencies["instance"],
        player=dependencies["player"],
        resolver=dependencies["resolver"],
    )

    def start_track(entry):
        if entry == playlist.entries[0]:
            controller.on_playback_error(None)
        else:
            controller.on_track_end(None)

    controller.start_track = Mock(side_effect=start_track)

    controller.run()

    assert controller.start_track.call_args_list == [
        ((playlist.entries[0],),),
        ((playlist.entries[1],),),
    ]
