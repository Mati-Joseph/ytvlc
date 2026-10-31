import json
import os
import shutil
import subprocess

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .playlist import clean_playlist_url


class ExtractorError(Exception):
    """Base exception for playlist extraction errors."""


class YtDlpNotFoundError(ExtractorError):
    """Raised when yt-dlp cannot be located."""


class PlaylistExtractionError(ExtractorError):
    """Raised when yt-dlp fails to extract a playlist."""


@dataclass(frozen=True)
class PlaylistEntry:
    video_id: str
    title: str
    index: int
    url: str


@dataclass(frozen=True)
class Playlist:
    title: str
    playlist_id: str
    entries: list[PlaylistEntry]
    unavailable_count: int


def find_ytdlp() -> str:
    """Find the preferred yt-dlp executable."""

    # Prefer the newer pipx installation over the Ubuntu APT version.
    pipx_path = Path.home() / ".local/bin/yt-dlp"

    if pipx_path.is_file() and os.access(pipx_path, os.X_OK):
        return str(pipx_path)

    executable = shutil.which("yt-dlp")

    if executable:
        return executable

    raise YtDlpNotFoundError(
        "yt-dlp was not found. Install it before continuing."
    )


def extract_playlist(
    raw_url: str,
    *,
    ytdlp_path: str | None = None,
    timeout: int = 180,
) -> Playlist:
    """Extract playlist metadata without downloading videos."""

    playlist_url = clean_playlist_url(raw_url)
    executable = ytdlp_path or find_ytdlp()

    command = [
        executable,
        "--ignore-config",
        "--js-runtimes",
        "node",
        "--flat-playlist",
        "--dump-single-json",
        "--no-warnings",
        playlist_url,
    ]

    try:
        result = subprocess.run(
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
    except subprocess.TimeoutExpired as exc:
        raise PlaylistExtractionError(
            f"Playlist extraction exceeded {timeout} seconds."
        ) from exc

    if result.returncode != 0:
        error = result.stderr.strip() or "Unknown yt-dlp error."

        raise PlaylistExtractionError(error)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PlaylistExtractionError(
            "yt-dlp returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise PlaylistExtractionError(
            "Unexpected playlist response."
        )

    raw_entries = data.get("entries")

    if not isinstance(raw_entries, list):
        raise PlaylistExtractionError(
            "The response does not contain a valid playlist."
        )

    playlist_id = parse_qs(
        urlparse(playlist_url).query
    ).get("list", [""])[0]

    entries = []
    unavailable_count = 0

    for position, item in enumerate(raw_entries, start=1):
        if not isinstance(item, dict) or not item.get("id"):
            unavailable_count += 1
            continue

        video_id = item["id"]

        entries.append(
            PlaylistEntry(
                video_id=video_id,
                title=item.get("title") or f"Untitled ({video_id})",
                index=item.get("playlist_index") or position,
                url=f"https://www.youtube.com/watch?v={video_id}",
            )
        )

    return Playlist(
        title=data.get("title") or "Untitled playlist",
        playlist_id=playlist_id,
        entries=entries,
        unavailable_count=unavailable_count,
    )