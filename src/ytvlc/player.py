import shutil
import subprocess
from urllib.parse import urlparse


class VLCNotFoundError(Exception):
    """Raised when VLC cannot be located."""


class PlaybackError(Exception):
    """Raised when VLC cannot start playback."""


def find_vlc() -> str:
    """Find the VLC executable."""

    executable = shutil.which("vlc")

    if not executable:
        raise VLCNotFoundError(
            "VLC was not found. Install VLC before continuing."
        )

    return executable


def play_stream(
    stream_url: str,
    *,
    vlc_path: str | None = None,
) -> subprocess.Popen:
    """Launch VLC with a resolved stream URL."""

    if not isinstance(stream_url, str) or not stream_url.strip():
        raise PlaybackError("A stream URL is required.")

    parsed = urlparse(stream_url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PlaybackError("The stream URL is invalid.")

    executable = vlc_path or find_vlc()

    command = [
        executable,
        "--no-one-instance",
        "--play-and-exit",
        stream_url,
    ]

    try:
        return subprocess.Popen(command)
    except FileNotFoundError as exc:
        raise VLCNotFoundError(
            f"Cannot execute VLC: {executable}"
        ) from exc
    except OSError as exc:
        raise PlaybackError(
            f"Could not start VLC: {exc}"
        ) from exc
