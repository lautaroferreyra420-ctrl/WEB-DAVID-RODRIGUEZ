import smtplib
import socket

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Envía un mail de prueba con la configuración de correo del .env y explica cualquier error."

    def add_arguments(self, parser):
        parser.add_argument('destino', nargs='?', default=None, help="Casilla que recibe la prueba (por defecto, la de consultas).")

    def handle(self, *args, **opciones):
        destino = opciones['destino'] or settings.EMAIL_DESTINO_CONSULTAS
        self.stdout.write("Configuración de correo:")
        self.stdout.write(f"  Servidor:   {settings.EMAIL_HOST}:{settings.EMAIL_PORT} "
                          f"({'SSL' if settings.EMAIL_USE_SSL else 'TLS' if settings.EMAIL_USE_TLS else 'sin cifrado'})")
        self.stdout.write(f"  Usuario:    {settings.EMAIL_HOST_USER or '(vacío)'}")
        self.stdout.write(f"  Contraseña: {'cargada' if settings.EMAIL_HOST_PASSWORD else '(vacía)'}")
        self.stdout.write(f"  Envía como: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"  Destino:    {destino}\n")

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise CommandError(
                "Faltan EMAIL_HOST_USER y/o EMAIL_HOST_PASSWORD en el archivo .env. "
                "Completalos (ver .env.example) y volvé a probar."
            )

        try:
            EmailMessage(
                subject="Prueba de correo - David Rodríguez Propiedades",
                body=(
                    "Este es un mail de prueba enviado desde la web.\n\n"
                    "Si lo estás leyendo, las consultas de los formularios van a llegar a esta casilla."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destino],
            ).send(fail_silently=False)
        except smtplib.SMTPAuthenticationError:
            raise CommandError(
                "El servidor rechazó el usuario o la contraseña. "
                "En Gmail hay que usar una «contraseña de aplicación» (requiere verificación en dos pasos)."
            )
        except (smtplib.SMTPConnectError, socket.gaierror, TimeoutError, ConnectionRefusedError):
            raise CommandError(
                "No pude conectarme al servidor. Revisá EMAIL_HOST, EMAIL_PORT y si usa TLS (587) o SSL (465)."
            )
        except smtplib.SMTPException as exc:
            raise CommandError(f"El servidor de correo devolvió un error: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Listo: mail de prueba enviado a {destino}. Revisá la bandeja (y spam)."))
