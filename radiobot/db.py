import sqlite3
from pathlib import Path


class TrackDB:
    """Remembers which videos were already uploaded, so reposts are skipped."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                video_id   TEXT PRIMARY KEY,
                status     TEXT NOT NULL,
                artist     TEXT,
                title      TEXT,
                detail     TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def is_uploaded(self, video_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM tracks WHERE video_id = ? AND status = 'uploaded'", (video_id,)
        ).fetchone()
        return row is not None

    def save(self, video_id: str, status: str, artist=None, title=None, detail=None) -> None:
        self.conn.execute(
            """
            INSERT INTO tracks (video_id, status, artist, title, detail)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                status = excluded.status, artist = excluded.artist, title = excluded.title,
                detail = excluded.detail, updated_at = CURRENT_TIMESTAMP
            """,
            (video_id, status, artist, title, detail),
        )
        self.conn.commit()
