FROM python:3.12-slim

# ffmpeg converts audio to mp3; deno is the JS runtime yt-dlp needs for YouTube
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=denoland/deno:bin-2.9.7 /deno /usr/local/bin/deno

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY radiobot ./radiobot

RUN useradd --create-home bot && mkdir -p /app/data && chown bot:bot /app/data
USER bot

CMD ["python", "bot.py"]
