# Publicar la web en un servidor (VPS Ubuntu)

Estos scripts instalan y actualizan la web como **servicio** (gunicorn + nginx) siguiendo las convenciones
del VPS compartido de Donweb: usuario propio (`davidprop`), carpeta `/opt/david-propiedades`, servicio
systemd y nginx como único punto de entrada.

## Cómo queda ordenado el servidor

```
/opt/david-propiedades/
├── app/                     el código (se puede reemplazar sin miedo)
├── venv/                    entorno de Python
├── data/                    LO IMPORTANTE: base de datos (db.sqlite3), fotos (media/) y estáticos
├── .env                     configuración y claves (permisos 600, nunca va a Git)
└── credenciales_admin.txt   usuario y clave del admin de la demo (solo root)
```

## Actualizar el código de la demo
1. Armar el paquete con el código (`git ls-files -co --exclude-standard -z | xargs -0 tar -czf app.tar.gz`).
2. Subir `app.tar.gz` y `actualizar.sh` a `/tmp/dr-deploy/` en el servidor.
3. Ejecutar `bash /tmp/dr-deploy/actualizar.sh`. No toca la base de datos, las fotos ni el `.env`.

## Mudarla a otro servidor con su dominio
1. En el servidor nuevo, subir a `/tmp/dr-deploy/`: `app.tar.gz`, `media.tar.gz` (carpeta `data/media`),
   `db.sqlite3` (de `data/`), `instalar.sh`, `servicio.tpl` y `nginx.tpl`.
2. Ejecutar `HOST=midominio.com bash /tmp/dr-deploy/instalar.sh`.
3. Apuntar el DNS (registro A) del dominio a la IP del servidor.
4. Activar HTTPS con `certbot --nginx -d midominio.com` y poner `USAR_HTTPS=True` en el `.env`.
5. En el `.env`: completar `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y, si se quiere la IA, `GEMINI_API_KEY`.
6. Sacar del `nginx.tpl` la línea `X-Robots-Tag` (es la que evita que Google indexe la demo).

> Ojo: el `instalar.sh` original está pensado para el VPS de Donweb (nginx ya instalado, puerto de SSH 5729).
