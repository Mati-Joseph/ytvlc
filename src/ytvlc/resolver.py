from subprocess import run, TimeoutExpired
from urllib.parse import urlparse

from .extractor import (
    PlaylistEntry,
    YtDlpNotFoundError,
    find_ytdlp,
)


class StreamResolutionError(Exception):
    """Raised when a video stream cannot be resolved."""


def resolve_stream(
    entry: PlaylistEntry,
    *,
    ytdlp_path: str | None = None,
    timeout: int = 60,
) -> str:
    """Resolve one YouTube playlist entry into a fresh stream URL."""

    executable = ytdlp_path or find_ytdlp()

    command = [
        executable,
        "--ignore-config",
        "--js-runtimes",
        "node",
        "--no-warnings",
        "--no-playlist",
        "--format",
        "best",
        "--get-url",
        entry.url,
    ]

    try:
        result = run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise YtDlpNotFoundError(
            f"Cannot execute yt-dlp: {executable}"
        ) from exc
    except TimeoutExpired as exc:
        raise StreamResolutionError(
            f"Stream resolution exceeded {timeout} seconds."
        ) from exc

    if result.returncode != 0:
        error = result.stderr.strip() or "Unknown yt-dlp error."
        raise StreamResolutionError(error)

    stream_url = result.stdout.strip()

    if not stream_url:
        raise StreamResolutionError(
            "yt-dlp returned an empty stream URL."
        )

    # The 'best' format should produce one combined audio/video URL.
    if len(stream_url.splitlines()) != 1:
        raise StreamResolutionError(
            "yt-dlp returned multiple stream URLs; expected one."
        )

    parsed = urlparse(stream_url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise StreamResolutionError(
            "yt-dlp returned an invalid stream URL."
        )

    return stream_url
