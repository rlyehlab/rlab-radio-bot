import re
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL

YOUTUBE_ID_RE = re.compile(
    r"(?:https?://)?(?:www\.|m\.|music\.)?"
    r"(?:youtube\.com/(?:watch\?(?:\S*?&)?v=|shorts/|live/|embed/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})"
)
# "Artist - Title", also with en/em dashes
ARTIST_TITLE_RE = re.compile(r"^(?P<artist>.+?)\s+[-–—]\s+(?P<title>.+)$")


class SkipVideo(Exception):
    """The video is valid but should not go to the radio (too long, live...)."""


@dataclass
class Track:
    video_id: str
    path: Path
    artist: str
    title: str

    @property
    def filename(self) -> str:
        name = f"{self.artist} - {self.title} [{self.video_id}].mp3"
        return re.sub(r'[\\/:*?"<>|]+', "_", name)


def extract_video_ids(text: str) -> list[str]:
    """Return the YouTube video ids found in text, unique and in order."""
    return list(dict.fromkeys(YOUTUBE_ID_RE.findall(text or "")))


def guess_artist_title(info: dict) -> tuple[str, str]:
    if info.get("artist") and info.get("track"):
        return info["artist"], info["track"]
    title = info.get("title") or info["id"]
    match = ARTIST_TITLE_RE.match(title)
    if match:
        return match["artist"].strip(), match["title"].strip()
    uploader = (info.get("uploader") or "Unknown").removesuffix(" - Topic")
    return uploader, title


def download_audio(video_id: str, dest_dir: Path, max_duration: int) -> Track:
    """Download a video as tagged mp3. Blocking: run it in a thread."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(dest_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
            {"key": "FFmpegMetadata", "add_metadata": True},
            {"key": "EmbedThumbnail"},
        ],
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming"):
            raise SkipVideo("es un stream en vivo")
        duration = info.get("duration") or 0
        if duration > max_duration:
            raise SkipVideo(f"dura {duration // 60} min (máximo {max_duration // 60})")

        artist, title = guess_artist_title(info)
        # FFmpegMetadata writes these into the ID3 tags AzuraCast reads
        info["artist"], info["track"] = artist, title
        info = ydl.process_ie_result(info, download=True)

    path = Path(info["requested_downloads"][0]["filepath"])
    return Track(video_id=video_id, path=path, artist=artist, title=title)
