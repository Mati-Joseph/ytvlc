import pytest

from ytvlc.playlist import clean_playlist_url, PlaylistURLError


PLAYLIST_ID = "PLBp9AkPtJBw4"


def test_normal_playlist_url():
    url = f"https://youtube.com/playlist?list={PLAYLIST_ID}"

    result = clean_playlist_url(url)

    assert result == (
        f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    )


def test_markdown_escaped_ampersand():
    url = (
        f"https://youtube.com/playlist?list={PLAYLIST_ID}"
        r"\&si=sFBEsVxUFjS-2sqW"
    )

    result = clean_playlist_url(url)

    assert result == (
        f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    )


def test_html_escaped_ampersand():
    url = (
        f"https://youtube.com/playlist?list={PLAYLIST_ID}"
        "&amp;si=tracking"
    )

    result = clean_playlist_url(url)

    assert result == (
        f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    )


def test_markdown_link():
    url = (
        f"[Kanye Playlist](https://youtube.com/playlist"
        f"?list={PLAYLIST_ID}&si=tracking)"
    )

    result = clean_playlist_url(url)

    assert result == (
        f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    )


def test_tracking_parameters_are_removed():
    url = (
        f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
        "&si=tracking&feature=shared"
    )

    result = clean_playlist_url(url)

    assert result == (
        f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    )


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://example.com/playlist?list=123",
        "https://youtube.com/watch?v=123",
        "https://youtube.com/playlist",
        "https://youtube.com/playlist?list=invalid%21id",
        "ftp://youtube.com/playlist?list=123",
    ],
)
def test_invalid_playlist_urls(url):
    with pytest.raises(PlaylistURLError):
        clean_playlist_url(url)