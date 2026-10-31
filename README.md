# ytvlc

A lightweight Linux command-line tool for playing YouTube playlists sequentially in VLC without downloading videos.

## Motivation

The project originated from a need to retain Last.fm scrobbling while playing YouTube playlists through VLC.

## Features

- Extract YouTube playlist entries using yt-dlp.
- Preserve the original playlist order.
- Resolve video streams on demand.
- Play tracks sequentially through VLC.
- Skip tracks when stream resolution or playback fails.
- Handle Markdown-escaped playlist URLs.
- Clean up VLC resources when playback ends or is interrupted.
- Provide a command-line interface with argument validation.

## Requirements

- Linux
- Python 3.12 or later
- VLC media player and its libVLC libraries
- yt-dlp
- Node.js (for yt-dlp JavaScript challenge support)

## Installation

Install the external requirements first:

- [VLC](https://www.videolan.org/vlc/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Node.js](https://nodejs.org/)

From the project root, install the Python dependencies and the editable project:

```bash
pipenv install --dev
```
