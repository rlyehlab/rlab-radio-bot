import logging

from telegram import Update
from telegram.ext import Application, MessageHandler, filters

from radiobot.azura import AzuraClient
from radiobot.config import Config
from radiobot.db import TrackDB
from radiobot.handlers import on_channel_post

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
# httpx logs every Telegram poll at INFO, including the URL with the bot token
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("radiobot")


def channel_filter(channel: str) -> filters.BaseFilter:
    if channel.startswith("@"):
        return filters.Chat(username=channel)
    return filters.Chat(chat_id=int(channel))


async def shutdown(app: Application) -> None:
    await app.bot_data["azura"].close()


def main() -> None:
    config = Config.from_env()

    app = Application.builder().token(config.telegram_token).post_shutdown(shutdown).build()
    app.bot_data["config"] = config
    app.bot_data["db"] = TrackDB(config.data_dir / "tracks.db")
    app.bot_data["azura"] = AzuraClient(
        config.azura_url, config.azura_api_key, config.azura_station
    )

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST & channel_filter(config.telegram_channel),
            on_channel_post,
        )
    )

    log.info("Listening to %s, uploading to %s", config.telegram_channel, config.azura_url)
    app.run_polling(allowed_updates=[Update.CHANNEL_POST])


if __name__ == "__main__":
    main()
