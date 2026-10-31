from subprocess import CompletedProcess, TimeoutExpired

import pytest

from ytvlc.extractor import PlaylistEntry, YtDlpNotFoundError
from ytvlc.resolver import StreamResolutionError, resolve_stream


@pytest.fixture
def entry():
    return PlaylistEntry(
        video_id="5S6az6odzPI",
        title="Ghost Town",
        index=1,
        url="https://www.youtube.com/watch?v=5S6az6odzPI",
    )


def test_resolves_stream_url(monkeypatch, entry):
    expected_url = "https://example.com/video.mp4"

    monkeypatch.setattr(
        "ytvlc.resolver.find_ytdlp",
        lambda: "/usr/local/bin/yt-dlp",
    )

    def fake_run(command, **kwargs):
        assert "--ignore-config" in command
        assert "--js-runtimes" in command
        assert "node" in command
        assert "--no-playlist" in command
        assert "--get-url" in command
        assert entry.url in command

        return CompletedProcess(
            command,
            0,
            stdout=expected_url + "\n",
            stderr="",
        )

    monkeypatch.setattr("ytvlc.resolver.run", fake_run)

    assert resolve_stream(entry) == expected_url


def test_raises_when_ytdlp_fails(monkeypatch, entry):
    monkeypatch.setattr(
        "ytvlc.resolver.find_ytdlp",
        lambda: "/usr/local/bin/yt-dlp",
    )

    monkeypatch.setattr(
        "ytvlc.resolver.run",
        lambda *args, **kwargs: CompletedProcess(
            args[0],
            1,
            stdout="",
            stderr="Video unavailable",
        ),
    )

    with pytest.raises(StreamResolutionError, match="Video unavailable"):
        resolve_stream(entry)


def test_raises_when_output_is_empty(monkeypatch, entry):
    monkeypatch.setattr(
        "ytvlc.resolver.find_ytdlp",
        lambda: "/usr/local/bin/yt-dlp",
    )

    monkeypatch.setattr(
        "ytvlc.resolver.run",
        lambda *args, **kwargs: CompletedProcess(
            args[0],
            0,
            stdout="",
            stderr="",
        ),
    )

    with pytest.raises(StreamResolutionError, match="empty stream URL"):
        resolve_stream(entry)


def test_raises_on_timeout(monkeypatch, entry):
    monkeypatch.setattr(
        "ytvlc.resolver.find_ytdlp",
        lambda: "/usr/local/bin/yt-dlp",
    )

    def fake_run(*args, **kwargs):
        raise TimeoutExpired(args[0], timeout=60)

    monkeypatch.setattr("ytvlc.resolver.run", fake_run)

    with pytest.raises(StreamResolutionError, match="exceeded 60 seconds"):
        resolve_stream(entry)


def test_raises_when_ytdlp_is_not_found(monkeypatch, entry):
    def fake_find_ytdlp():
        raise YtDlpNotFoundError("yt-dlp not found")

    monkeypatch.setattr(
        "ytvlc.resolver.find_ytdlp",
        fake_find_ytdlp,
    )

    with pytest.raises(YtDlpNotFoundError):
        resolve_stream(entry)
