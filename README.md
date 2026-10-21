# rlab-radio-bot

Bot de Telegram que escucha un canal y, cada vez que alguien publica un link de YouTube, descarga el audio y lo sube a la radio de rlab (AzuraCast, `adminradio.rlab.lat`).

```
canal de Telegram ──► bot ──► yt-dlp (mp3 + tags + tapa) ──► API de AzuraCast ──► carpeta "telegram/"
```

- Detecta links `youtube.com/watch`, `youtu.be`, `music.youtube.com` y `shorts`, también en links con formato y en descripciones de fotos o videos.
- Saltea streams en vivo y videos más largos que `MAX_DURATION` (15 min por defecto).
- Guarda en SQLite los videos ya subidos, así un tema repetido no se sube dos veces.
- Escribe artista y título en los tags del mp3 (sacados de YouTube Music o del título "Artista - Tema"), para que se vea bien en "suena ahora".

## Configuración

### 1. Bot de Telegram

1. Crear el bot con [@BotFather](https://t.me/BotFather) y copiar el token.
2. Agregar el bot como **administrador** del canal. Con eso recibe los posts. Si `REPLY_IN_CHANNEL=true`, también necesita permiso para publicar.

### 2. AzuraCast

1. En *My Account → API Keys* crear una API key. El usuario tiene que tener permiso de *Manage Station Media* en la estación.
2. En la estación, crear una playlist (por ejemplo "Telegram").
3. En *Music Files*, crear la carpeta `telegram`, seleccionarla y en *Set or Clear Playlists* asignarle la playlist. Todo lo que el bot suba a esa carpeta entra solo en rotación.

### 3. Variables de entorno

```sh
cp .env.example .env
```

| Variable | Descripción |
|---|---|
| `TELEGRAM_TOKEN` | Token de BotFather |
| `TELEGRAM_CHANNEL` | `@usuario` del canal o su id numérico (`-100…`) |
| `AZURA_URL` | `https://adminradio.rlab.lat` |
| `AZURA_API_KEY` | API key de AzuraCast |
| `AZURA_STATION` | Shortcode de la estación (`rlab_radio`) |
| `AZURA_FOLDER` | Carpeta de destino (`telegram`) |
| `MAX_DURATION` | Duración máxima en segundos (`900`) |
| `REPLY_IN_CHANNEL` | `true` para responder en el canal cuando se agrega o saltea un tema |

## Correr

```sh
docker compose up -d --build
docker compose logs -f
```

Local, sin Docker (necesita `ffmpeg` y [`deno`](https://deno.com) instalados):

```sh
python -m venv venv && . venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## CI / Deploy

`.github/workflows/ci.yml`, igual que en `Bot-telegram`:

- **build**: `ruff check`, `pytest` y `docker build` en cada push y PR a `main`.
- **deploy**: en push a `main`, entra por SSH al servidor, hace `git pull` y reconstruye la imagen. Usa los secrets `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `SSH_PORT` y `DEPLOY_PATH`.

El `.env` vive solo en el servidor, en `DEPLOY_PATH`. El deploy reconstruye sin caché para instalar siempre la última versión de `yt-dlp`, porque YouTube rompe las versiones viejas seguido. Si el bot deja de descargar, lo primero es redeployar: en GitHub, *Actions → CI / Deploy → Run workflow* sobre `main` (`workflow_dispatch`).

## Problemas comunes

- **No llegan los posts**: el bot tiene que ser admin del canal. Revisar que `TELEGRAM_CHANNEL` coincida.
- **`Sign in to confirm you're not a bot`**: YouTube está bloqueando la IP del servidor. Actualizar yt-dlp (redeploy). Si sigue, ver las opciones de cookies en la [wiki de yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp).
- **Error 413 al subir**: el nginx de AzuraCast (o un proxy delante) limita el tamaño del request. El mp3 viaja en base64, así que pesa ~33% más. Subir ese límite o bajar `MAX_DURATION`.
- **Ver qué pasó con un video**: `docker compose exec bot python -c "import sqlite3; [print(r) for r in sqlite3.connect('data/tracks.db').execute('select * from tracks order by updated_at desc limit 20')]"`
