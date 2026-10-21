import asyncio
import logging
import tempfile
from pathlib import Path

import httpx
from telegram import Message, MessageEntity, Update
from telegram.ext import ContextTypes

from radiobot.youtube import SkipVideo, download_audio, extract_video_ids

log = logging.getLogger(__name__)


def message_text(message: Message) -> str:
    """Text plus the URLs hidden behind formatted links."""
    parts = [message.text or message.caption or ""]
    entities = list(message.entities or ()) + list(message.caption_entities or ())
    parts += [e.url for e in entities if e.type == MessageEntity.TEXT_LINK and e.url]
    return "\n".join(parts)


async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    video_ids = extract_video_ids(message_text(message))
    if not video_ids:
        return

    config = context.bot_data["config"]
    db = context.bot_data["db"]
    for video_id in video_ids:
        if db.is_uploaded(video_id):
            log.info("%s already uploaded, skipping", video_id)
            continue
        reply = await process_video(video_id, context)
        if reply and config.reply_in_channel:
            await message.reply_text(reply, disable_web_page_preview=True)


async def process_video(video_id: str, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Download and upload one video. Returns the text to reply with."""
    config = context.bot_data["config"]
    db = context.bot_data["db"]
    azura = context.bot_data["azura"]

    with tempfile.TemporaryDirectory() as tmp:
        try:
            track = await asyncio.to_thread(
                download_audio, video_id, Path(tmp), config.max_duration
            )
        except SkipVideo as e:
            log.info("%s skipped: %s", video_id, e)
            db.save(video_id, "skipped", detail=str(e))
            return f"⏭ No se agrega a la radio: {e}."
        except Exception as e:
            log.exception("%s download failed", video_id)
            db.save(video_id, "failed", detail=str(e))
            return None

        remote_path = f"{config.azura_folder}/{track.filename}"
        try:
            await azura.upload(track.path, remote_path)
        except httpx.HTTPError as e:
            log.exception("%s upload failed", video_id)
            db.save(video_id, "failed", track.artist, track.title, f"upload: {e}")
            return None

    db.save(video_id, "uploaded", track.artist, track.title, remote_path)
    log.info("%s uploaded as %s", video_id, remote_path)
    return f"📻 Agregado a la radio: {track.artist} - {track.title}"
