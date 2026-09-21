#!/bin/bash
# Actualiza SOLO el código de la demo (no toca la base de datos, las fotos ni el .env).
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a

APP=david-propiedades
BASE=/opt/$APP
USUARIO=davidprop
SUBIDA=/tmp/dr-deploy
como_app() { sudo -u "$USUARIO" bash -c "set -a; . $BASE/.env; set +a; cd $BASE/app; $*"; }

echo "== Código nuevo"
sudo tar -xzf "$SUBIDA/app.tar.gz" -C "$BASE/app"
sudo chown -R "$USUARIO:$USUARIO" "$BASE/app"

echo "== Dependencias, migraciones y estáticos"
sudo -u "$USUARIO" "$BASE/venv/bin/pip" install --quiet -r "$BASE/app/requirements.txt"
como_app "$BASE/venv/bin/python manage.py migrate --noinput" | tail -1
como_app "$BASE/venv/bin/python manage.py collectstatic --noinput" | tail -1

echo "== Reinicio del servicio"
sudo systemctl restart "$APP"
sleep 3
echo "estado: $(systemctl is-active $APP)"
