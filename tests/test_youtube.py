from radiobot.youtube import Track, extract_video_ids, guess_artist_title


def test_extracts_common_url_formats():
    text = """
    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    youtu.be/3JZ_D3ELwOQ?si=abc
    https://music.youtube.com/watch?list=PL1&v=kJQP7kiw5Fk
    https://youtube.com/shorts/aBcDeFgHiJk
    """
    assert extract_video_ids(text) == [
        "dQw4w9WgXcQ",
        "3JZ_D3ELwOQ",
        "kJQP7kiw5Fk",
        "aBcDeFgHiJk",
    ]


def test_dedupes_and_ignores_other_links():
    text = "https://youtu.be/dQw4w9WgXcQ https://youtu.be/dQw4w9WgXcQ https://rlab.lat"
    assert extract_video_ids(text) == ["dQw4w9WgXcQ"]
    assert extract_video_ids("") == []


def test_artist_title_from_music_metadata():
    info = {"id": "x", "title": "whatever", "artist": "Sumo", "track": "Mañana en el Abasto"}
    assert guess_artist_title(info) == ("Sumo", "Mañana en el Abasto")


def test_artist_title_from_video_title():
    info = {"id": "x", "title": "Virus – Wadu Wadu (Official Video)", "uploader": "chan"}
    assert guess_artist_title(info) == ("Virus", "Wadu Wadu (Official Video)")


def test_artist_title_falls_back_to_uploader():
    info = {"id": "x", "title": "Live set", "uploader": "Soda Stereo - Topic"}
    assert guess_artist_title(info) == ("Soda Stereo", "Live set")


def test_filename_is_safe():
    track = Track("dQw4w9WgXcQ", None, "AC/DC", 'Who? "Me"')
    assert track.filename == "AC_DC - Who_ _Me_ [dQw4w9WgXcQ].mp3"
