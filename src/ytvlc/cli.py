
import argparse
import sys

from .controller import PlaybackController
from .extractor import ExtractorError, extract_playlist
from .playlist import PlaylistURLError


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="ytvlc",
        description=(
            "Play YouTube playlists sequentially "
            "in VLC without downloading videos."
        ),
    )

    parser.add_argument(
        "playlist_url",
        metavar="PLAYLIST_URL",
        help="URL of the YouTube playlist to play.",
    )

    return parser


def main(argv=None) -> int:
    """Run the ytvlc command-line application."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        playlist = extract_playlist(args.playlist_url)

    except (PlaylistURLError, ExtractorError) as exc:
        print(f"ytvlc: error: {exc}", file=sys.stderr)
        return 1

    if not playlist.entries:
        print(
            "ytvlc: error: no playable videos were found.",
            file=sys.stderr,
        )
        return 1

    print(f"\nPlaylist: {playlist.title}")
    print(f"Available tracks: {len(playlist.entries)}")

    if playlist.unavailable_count:
        print(
            f"Unavailable entries: {playlist.unavailable_count}"
        )

    print("\nStarting playback...")

    try:
        controller = PlaybackController(playlist)
        controller.run()

    except KeyboardInterrupt:
        print("\nPlayback interrupted.", file=sys.stderr)
        return 130

    except (ExtractorError, RuntimeError) as exc:
        print(f"ytvlc: error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
