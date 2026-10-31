import re
from urllib.parse import parse_qs, urlparse


YOUTUBE_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}


class PlaylistURLError(ValueError):
    """Raised when a YouTube playlist URL is invalid."""


def clean_playlist_url(raw_url: str) -> str:
    """Extract and normalise a YouTube playlist URL."""

    if not isinstance(raw_url, str) or not raw_url.strip():
        raise PlaylistURLError("A playlist URL is required.")

    raw_url = raw_url.strip()

    # Extract the URL from a Markdown link: [title](URL)
    markdown_match = re.fullmatch(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        raw_url,
    )

    if markdown_match:
        raw_url = markdown_match.group(2)

    # Remove formatting escapes, not arbitrary URL backslashes.
    raw_url = raw_url.replace(r"\&", "&")
    raw_url = raw_url.replace("&amp;", "&")

    # Remove surrounding angle brackets, if present.
    if raw_url.startswith("<") and raw_url.endswith(">"):
        raw_url = raw_url[1:-1]

    parsed = urlparse(raw_url)

    if parsed.scheme not in {"http", "https"}:
        raise PlaylistURLError("The URL must use HTTP or HTTPS.")

    if parsed.hostname not in YOUTUBE_DOMAINS:
        raise PlaylistURLError("The URL must belong to YouTube.")

    if parsed.path != "/playlist":
        raise PlaylistURLError("The URL must point to a YouTube playlist.")

    query = parse_qs(parsed.query)
    playlist_ids = query.get("list", [])

    if not playlist_ids:
        raise PlaylistURLError("No playlist ID was found in the URL.")

    playlist_id = playlist_ids[0]

    if not re.fullmatch(r"[A-Za-z0-9_-]+", playlist_id):
        raise PlaylistURLError("The playlist ID contains invalid characters.")

    return f"https://www.youtube.com/playlist?list={playlist_id}"