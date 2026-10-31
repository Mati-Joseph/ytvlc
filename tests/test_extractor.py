import json
import subprocess

import pytest

from ytvlc.extractor import (
    extract_playlist,
    PlaylistExtractionError,
    YtDlpNotFoundError,
)


PLAYLIST_URL = (
    "https://youtube.com/playlist?list=PLBp9AkPtJBw4"
)

MOCK_RESPONSE = {
    "title": "kanye",
    "entries": [
        {
            "id": "5S6az6odzPI",
            "title": "Ghost Town",
            "playlist_index": 1,
        },
        {
            "id": "IetxV6YWv1c",
            "title": "No Church In The Wild",
            "playlist_index": 2,
        },
        {
            "id": "YGiBUN6EjCo",
            "title": "Mercy",
            "playlist_index": 302,
        },
    ],
}


def test_extract_playlist(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(MOCK_RESPONSE),
            "",
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    playlist = extract_playlist(
        PLAYLIST_URL,
        ytdlp_path="yt-dlp",
    )

    assert playlist.title == "kanye"
    assert playlist.playlist_id == "PLBp9AkPtJBw4"
    assert len(playlist.entries) == 3
    assert playlist.unavailable_count == 0


def test_entries_preserve_playlist_order(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, json.dumps(MOCK_RESPONSE), ""
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    playlist = extract_playlist(
        PLAYLIST_URL,
        ytdlp_path="yt-dlp",
    )

    assert [
        entry.title for entry in playlist.entries
    ] == [
        "Ghost Town",
        "No Church In The Wild",
        "Mercy",
    ]


def test_entry_contains_watch_url(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, json.dumps(MOCK_RESPONSE), ""
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    playlist = extract_playlist(
        PLAYLIST_URL,
        ytdlp_path="yt-dlp",
    )

    assert playlist.entries[0].url == (
        "https://www.youtube.com/watch?v=5S6az6odzPI"
    )


def test_unavailable_entries_are_skipped(monkeypatch):
    response = {
        "title": "Test playlist",
        "entries": [
            {
                "id": "video123",
                "title": "Available video",
                "playlist_index": 1,
            },
            None,
            {
                "title": "Unavailable video",
            },
        ],
    }

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, json.dumps(response), ""
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    playlist = extract_playlist(
        PLAYLIST_URL,
        ytdlp_path="yt-dlp",
    )

    assert len(playlist.entries) == 1
    assert playlist.unavailable_count == 2


def test_failed_ytdlp_execution(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 1, "", "YouTube extraction failed."
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    with pytest.raises(
        PlaylistExtractionError,
        match="YouTube extraction failed",
    ):
        extract_playlist(
            PLAYLIST_URL,
            ytdlp_path="yt-dlp",
        )


def test_invalid_json_response(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, "not valid json", ""
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    with pytest.raises(
        PlaylistExtractionError,
        match="invalid JSON",
    ):
        extract_playlist(
            PLAYLIST_URL,
            ytdlp_path="yt-dlp",
        )


def test_extraction_timeout(monkeypatch):
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(
            command, timeout=180
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    with pytest.raises(
        PlaylistExtractionError,
        match="exceeded 180 seconds",
    ):
        extract_playlist(
            PLAYLIST_URL,
            ytdlp_path="yt-dlp",
        )


def test_js_runtime_and_playlist_flags(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command

        return subprocess.CompletedProcess(
            command, 0, json.dumps(MOCK_RESPONSE), ""
        )

    monkeypatch.setattr(
        "ytvlc.extractor.subprocess.run",
        fake_run,
    )

    extract_playlist(
        PLAYLIST_URL,
        ytdlp_path="yt-dlp",
    )

    command = captured["command"]

    assert "--ignore-config" in command
    assert "--js-runtimes" in command
    assert "node" in command
    assert "--flat-playlist" in command
    assert "--dump-single-json" in command