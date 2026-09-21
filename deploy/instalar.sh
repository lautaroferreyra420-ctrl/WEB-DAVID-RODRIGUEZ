#!/bin/bash
# Instala la web David Rodríguez Propiedades (Django) en el VPS de Donweb como DEMO, siguiendo las
# convenciones del servidor: usuario dedicado, /opt/<app>, systemd, nginx como único punto de entrada.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a

APP=david-propiedades
BASE=/opt/$APP
USUARIO=davidprop
PUERTO=${PUERTO:-8010}
HOST=${HOST:-david-demo.149.50.157.163.sslip.io}
DATOS=$BASE/data
SUBIDA=/tmp/dr-deploy

paso() { echo; echo "== $1"; }
como_app() { sudo -u "$USUARIO" bash -c "set -a; . $BASE/.env; set +a; cd $BASE/app; $*"; }

paso "1. Usuario dedicado y carpetas"
if ! id "$USUARIO" >/dev/null 2>&1; then
    sudo useradd -r -m -d "$BASE" -s /usr/sbin/nologin "$USUARIO"
    echo "usuario $USUARIO creado"
else
    echo "usuario $USUARIO ya existía"
fi
sudo mkdir -p "$BASE/app" "$DATOS"

paso "2. Código, base de datos y fotos"
sudo tar -xzf "$SUBIDA/app.tar.gz" -C "$BASE/app"
if [ ! -d "$DATOS/media" ]; then sudo tar -xzf "$SUBIDA/media.tar.gz" -C "$DATOS"; else echo "fotos: ya existían, no se tocan"; fi
if [ ! -f "$DATOS/db.sqlite3" ]; then sudo cp "$SUBIDA/db.sqlite3" "$DATOS/db.sqlite3"; else echo "base de datos: ya existía, no se toca"; fi
sudo chown -R "$USUARIO:$USUARIO" "$BASE"
sudo chmod 755 "$BASE" "$DATOS"
sudo chmod 640 "$DATOS/db.sqlite3"

paso "3. Entorno de Python y dependencias"
if [ ! -d "$BASE/venv" ]; then sudo -u "$USUARIO" python3 -m venv "$BASE/venv"; fi
sudo -u "$USUARIO" "$BASE/venv/bin/pip" install --quiet --upgrade pip
sudo -u "$USUARIO" "$BASE/venv/bin/pip" install --quiet -r "$BASE/app/requirements.txt"
echo "dependencias instaladas"

paso "4. Configuración (.env con permisos 600; los valores no se muestran)"
if [ ! -f "$BASE/.env" ]; then
    SECRETO=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    sudo tee "$BASE/.env" >/dev/null <<EOF
SECRET_KEY=$SECRETO
DEBUG=False
ALLOWED_HOSTS=$HOST
CSRF_TRUSTED_ORIGINS=http://$HOST,https://$HOST
DATA_DIR=$DATOS
USAR_HTTPS=False
WHATSAPP_NUMBER=5491133405963
EMAIL_DESTINO_CONSULTAS=info@davidrodriguezprop.com
EOF
    sudo chown "$USUARIO:$USUARIO" "$BASE/.env"
    sudo chmod 600 "$BASE/.env"
    echo ".env creado en $BASE/.env"
else
    echo ".env ya existía, no se toca"
fi

paso "5. Base de datos, estáticos y limpieza de sesiones"
como_app "$BASE/venv/bin/python manage.py migrate --noinput" | tail -2
como_app "$BASE/venv/bin/python manage.py collectstatic --noinput" | tail -1
como_app "$BASE/venv/bin/python manage.py shell -c \"from django.contrib.sessions.models import Session; print('sesiones borradas:', Session.objects.all().delete()[0])\"" | tail -1

paso "6. Clave nueva para el admin de la demo (queda en un archivo, no se muestra)"
if [ ! -f "$BASE/credenciales_admin.txt" ]; then
    CLAVE=$(python3 -c "import secrets; print(secrets.token_urlsafe(14))")
    USUARIO_ADMIN=$(sudo -u "$USUARIO" bash -c "set -a; . $BASE/.env; set +a; cd $BASE/app; DR_CLAVE='$CLAVE' $BASE/venv/bin/python manage.py shell -c \"import os; from django.contrib.auth import get_user_model; U=get_user_model(); u=U.objects.filter(is_superuser=True).first(); u.set_password(os.environ['DR_CLAVE']); u.save(); print(u.username)\"" | tail -1)
    sudo install -m 600 -o root -g root /dev/null "$BASE/credenciales_admin.txt"
    printf 'Panel de administración de la demo\nUsuario: %s\nClave: %s\n' "$USUARIO_ADMIN" "$CLAVE" | sudo tee "$BASE/credenciales_admin.txt" >/dev/null
    echo "usuario del admin: $USUARIO_ADMIN | la clave quedó en $BASE/credenciales_admin.txt (solo root)"
else
    echo "credenciales ya existían, no se tocan"
fi

paso "7. Servicio systemd"
sed -e "s|@USUARIO@|$USUARIO|g" -e "s|@BASE@|$BASE|g" -e "s|@PUERTO@|$PUERTO|g" "$SUBIDA/servicio.tpl" | sudo tee "/etc/systemd/system/$APP.service" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now "$APP"
sleep 3
echo "estado del servicio: $(systemctl is-active $APP)"

paso "8. nginx (se valida antes de recargar)"
if [ -f "/etc/nginx/sites-enabled/$APP.conf" ]; then sudo cp -a "/etc/nginx/sites-enabled/$APP.conf" "/etc/nginx/sites-enabled/$APP.conf.bak.$(date +%Y%m%d%H%M%S)"; fi
sed -e "s|@HOST@|$HOST|g" -e "s|@DATOS@|$DATOS|g" -e "s|@PUERTO@|$PUERTO|g" "$SUBIDA/nginx.tpl" | sudo tee "/etc/nginx/sites-enabled/$APP.conf" >/dev/null
sudo nginx -t
sudo systemctl reload nginx
echo "nginx recargado (sin cortes)"

paso "9. Verificación desde el propio servidor"
for RUTA in / /nosotros/ /tasacion/ /mapa/ /static/css/style.css; do
    printf '%s -> ' "$RUTA"; curl -s -o /dev/null -w '%{http_code}\n' -H "Host: $HOST" "http://127.0.0.1$RUTA"
done
printf '/media/ (una foto) -> '
FOTO=$(cd "$DATOS/media/propiedades" && ls | head -1)
curl -s -o /dev/null -w '%{http_code}\n' -H "Host: $HOST" "http://127.0.0.1/media/propiedades/$FOTO"
echo; echo "Listo: http://$HOST"
