#!/usr/bin/env bash
# Открывает экран приложения. Аргумент — путь (/admin или /setup).
# Адрес берётся из app.conf. Если он локальный, бэкенд поднимается сам.

APP_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
BACKEND="$APP_DIR/backend"

APP_URL="http://127.0.0.1:8000"
[ -f "$APP_DIR/app.conf" ] && . "$APP_DIR/app.conf"

PATHQ="${1:-/admin}"

case "$APP_URL" in
  *127.0.0.1*|*localhost*)
    cd "$BACKEND" || exit 1
    if [ ! -d venv ]; then
      python3 -m venv venv
      venv/bin/pip install --upgrade pip
      venv/bin/pip install -r requirements.txt
    fi
    if ! curl -s -o /dev/null "$APP_URL/login" 2>/dev/null; then
      nohup venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 > "$BACKEND/app.log" 2>&1 &
      for _ in $(seq 1 40); do
        curl -s -o /dev/null "$APP_URL/login" 2>/dev/null && break
        sleep 0.25
      done
    fi
    ;;
esac

URL="$APP_URL$PATHQ"
for B in google-chrome google-chrome-stable chromium chromium-browser brave-browser; do
  if command -v "$B" >/dev/null 2>&1; then
    exec "$B" --app="$URL" --new-window
  fi
done
exec xdg-open "$URL"
