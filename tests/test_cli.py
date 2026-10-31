
from ytvlc.cli import main
from ytvlc.extractor import (
    Playlist,
    PlaylistEntry,
    PlaylistExtractionError,
)


def make_playlist(entries=None, unavailable_count=0):
    if entries is None:
        entries = [
            PlaylistEntry(
                video_id="video123",
                title="Test video",
                index=1,
                url="https://www.youtube.com/watch?v=video123",
            )
        ]

    return Playlist(
        title="Test playlist",
        playlist_id="test123",
        entries=entries,
        unavailable_count=unavailable_count,
    )


def test_main_starts_playback(monkeypatch, capsys):
    playlist = make_playlist()
    controller_called = {}

    monkeypatch.setattr(
        "ytvlc.cli.extract_playlist",
        lambda url: playlist,
    )

    class FakeController:
        def __init__(self, received_playlist):
            controller_called["playlist"] = received_playlist

        def run(self):
            controller_called["run"] = True

    monkeypatch.setattr(
        "ytvlc.cli.PlaybackController",
        FakeController,
    )

    result = main(["https://youtube.com/playlist?list=test123"])

    assert result == 0
    assert controller_called["playlist"] is playlist
    assert controller_called["run"] is True
    assert "Test playlist" in capsys.readouterr().out


def test_main_handles_extraction_error(monkeypatch, capsys):
    def fail_extraction(url):
        raise PlaylistExtractionError("Extraction failed")

    monkeypatch.setattr(
        "ytvlc.cli.extract_playlist",
        fail_extraction,
    )

    result = main(["https://youtube.com/playlist?list=test123"])

    assert result == 1
    assert "Extraction failed" in capsys.readouterr().err


def test_main_rejects_empty_playlist(monkeypatch, capsys):
    playlist = make_playlist(entries=[])

    monkeypatch.setattr(
        "ytvlc.cli.extract_playlist",
        lambda url: playlist,
    )

    result = main(["https://youtube.com/playlist?list=test123"])

    assert result == 1
    assert "no playable videos" in capsys.readouterr().err


def test_main_handles_missing_ytdlp(monkeypatch, capsys):
    def fail_extraction(url):
        raise PlaylistExtractionError("yt-dlp was not found")

    monkeypatch.setattr(
        "ytvlc.cli.extract_playlist",
        fail_extraction,
    )

    result = main(["https://youtube.com/playlist?list=test123"])

    assert result == 1
    assert "yt-dlp was not found" in capsys.readouterr().err


def test_main_returns_130_when_playback_is_interrupted(
    monkeypatch,
    capsys,
):
    playlist = make_playlist()

    monkeypatch.setattr(
        "ytvlc.cli.extract_playlist",
        lambda url: playlist,
    )

    class InterruptingController:
        def __init__(self, received_playlist):
            pass

        def run(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(
        "ytvlc.cli.PlaybackController",
        InterruptingController,
    )

    result = main(["https://youtube.com/playlist?list=test123"])

    assert result == 130
    assert "Playback interrupted" in capsys.readouterr().err


def test_main_handles_vlc_initialization_error(
    monkeypatch,
    capsys,
):
    playlist = make_playlist()

    monkeypatch.setattr(
        "ytvlc.cli.extract_playlist",
        lambda url: playlist,
    )

    class FailingController:
        def __init__(self, received_playlist):
            raise RuntimeError("Could not initialize VLC")

    monkeypatch.setattr(
        "ytvlc.cli.PlaybackController",
        FailingController,
    )

    result = main(["https://youtube.com/playlist?list=test123"])

    assert result == 1
    assert "Could not initialize VLC" in capsys.readouterr().err
