import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "si")


@dataclass(frozen=True)
class Config:
    telegram_token: str
    # Numeric id (-100...) or @username of the channel to listen to
    telegram_channel: str
    azura_url: str
    azura_api_key: str
    azura_station: str
    # Folder inside the station media where songs are uploaded
    azura_folder: str
    max_duration: int
    reply_in_channel: bool
    data_dir: Path

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            telegram_token=_required("TELEGRAM_TOKEN"),
            telegram_channel=_required("TELEGRAM_CHANNEL"),
            azura_url=_required("AZURA_URL").rstrip("/"),
            azura_api_key=_required("AZURA_API_KEY"),
            azura_station=os.getenv("AZURA_STATION", "rlab_radio"),
            azura_folder=os.getenv("AZURA_FOLDER", "telegram").strip("/"),
            max_duration=int(os.getenv("MAX_DURATION", "900")),
            reply_in_channel=_bool("REPLY_IN_CHANNEL"),
            data_dir=Path(os.getenv("DATA_DIR", "data")),
        )
