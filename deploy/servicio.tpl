[Unit]
Description=David Rodriguez Propiedades (Django + gunicorn)
After=network.target

[Service]
Type=simple
User=@USUARIO@
WorkingDirectory=@BASE@/app
ExecStart=@BASE@/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:@PUERTO@ --workers 2 --timeout 90
Restart=on-failure
EnvironmentFile=@BASE@/.env

[Install]
WantedBy=multi-user.target
