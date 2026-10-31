
from threading import Event

import vlc

from .extractor import Playlist
from .resolver import resolve_stream


class PlaybackController:
    """Manage sequential playback of a YouTube playlist."""

    def __init__(
        self,
        playlist: Playlist,
        *,
        instance=None,
        player=None,
        resolver=resolve_stream,
    ):
        self.playlist = playlist
        self.resolver = resolver

        self.instance = instance or vlc.Instance(
            "--no-video-title-show"
        )

        if self.instance is None:
            raise RuntimeError("Could not initialize VLC.")

        self.player = player or self.instance.media_player_new()

        self.track_finished = Event()
        self.playback_failed = Event()

        self.event_manager = self.player.event_manager()

        self.event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self.on_track_end,
        )

        self.event_manager.event_attach(
            vlc.EventType.MediaPlayerEncounteredError,
            self.on_playback_error,
        )

    def on_track_end(self, event):
        """Signal that the current track has finished."""
        self.track_finished.set()

    def on_playback_error(self, event):
        """Signal that VLC encountered a playback error."""
        self.playback_failed.set()

    def start_track(self, entry):
        """Resolve and start one playlist entry."""
        self.track_finished.clear()
        self.playback_failed.clear()

        stream_url = self.resolver(entry)
        media = self.instance.media_new(stream_url)

        self.player.set_media(media)

        result = self.player.play()

        if result == -1:
            raise RuntimeError(
                f"VLC could not start playback: {entry.title}"
            )

    def cleanup(self):
        """Stop playback and release VLC resources."""
        self.player.stop()
        self.player.release()
        self.instance.release()
