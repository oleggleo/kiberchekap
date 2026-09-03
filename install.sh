#!/usr/bin/env bash
# Ставит два ярлыка: «Заявки» и «Настройка». Запустить один раз.

set -e
APP_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
chmod +x "$APP_DIR/launch.sh"

APPS="$HOME/.local/share/applications"
mkdir -p "$APPS"

# старый общий ярлык больше не нужен
rm -f "$APPS/kiberchekap.desktop"

make_shortcut() {
  cat > "$APPS/$3" <<EOF
[Desktop Entry]
Type=Application
Name=$1
Comment=Киберчекап
Exec=$APP_DIR/launch.sh $2
Icon=$APP_DIR/assets/icon.svg
Terminal=false
Categories=Office;
StartupNotify=true
EOF
  chmod +x "$APPS/$3"
}

make_shortcut "Киберчекап — Заявки" "/admin" "kiberchekap-leads.desktop"
make_shortcut "Киберчекап — Настройка" "/setup" "kiberchekap-setup.desktop"
update-desktop-database "$APPS" 2>/dev/null || true

DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || true)
[ -z "$DESKTOP_DIR" ] && DESKTOP_DIR="$HOME/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
  rm -f "$DESKTOP_DIR/kiberchekap.desktop"
  cp "$APPS/kiberchekap-leads.desktop" "$APPS/kiberchekap-setup.desktop" "$DESKTOP_DIR/"
  chmod +x "$DESKTOP_DIR"/kiberchekap-*.desktop
  gio set "$DESKTOP_DIR/kiberchekap-leads.desktop" metadata::trusted true 2>/dev/null || true
  gio set "$DESKTOP_DIR/kiberchekap-setup.desktop" metadata::trusted true 2>/dev/null || true
fi

echo "Готово. Ярлыки «Заявки» и «Настройка» на рабочем столе и в меню."
