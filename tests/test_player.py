from unittest.mock import Mock

import pytest

from ytvlc.player import (
    PlaybackError,
    VLCNotFoundError,
    find_vlc,
    play_stream,
)


STREAM_URL = "https://example.com/video.mp4"


def test_find_vlc(monkeypatch):
    monkeypatch.setattr(
        "ytvlc.player.shutil.which",
        lambda name: "/usr/bin/vlc",
    )

    assert find_vlc() == "/usr/bin/vlc"


def test_find_vlc_when_missing(monkeypatch):
    monkeypatch.setattr(
        "ytvlc.player.shutil.which",
        lambda name: None,
    )

    with pytest.raises(VLCNotFoundError):
        find_vlc()


def test_play_stream_launches_vlc(monkeypatch):
    process = Mock()

    monkeypatch.setattr(
        "ytvlc.player.subprocess.Popen",
        lambda command: process,
    )

    result = play_stream(
        STREAM_URL,
        vlc_path="/usr/bin/vlc",
    )

    assert result is process


def test_play_stream_uses_expected_arguments(monkeypatch):
    captured = {}

    def fake_popen(command):
        captured["command"] = command
        return Mock()

    monkeypatch.setattr(
        "ytvlc.player.subprocess.Popen",
        fake_popen,
    )

    play_stream(STREAM_URL, vlc_path="/usr/bin/vlc")

    assert captured["command"] == [
        "/usr/bin/vlc",
        "--no-one-instance",
        "--play-and-exit",
        STREAM_URL,
    ]


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "ftp://example.com/video.mp4",
        "https:///video.mp4",
    ],
)
def test_play_stream_rejects_invalid_urls(url):
    with pytest.raises(PlaybackError):
        play_stream(url, vlc_path="/usr/bin/vlc")
