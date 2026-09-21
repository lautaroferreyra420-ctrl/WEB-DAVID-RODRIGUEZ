server {
    listen 80;
    listen [::]:80;
    server_name @HOST@;

    client_max_body_size 25m;

    # Es una demo: que Google no la indexe
    add_header X-Robots-Tag "noindex, nofollow" always;

    location /static/ {
        alias @DATOS@/staticfiles/;
        expires 7d;
    }

    location /media/ {
        alias @DATOS@/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:@PUERTO@;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
