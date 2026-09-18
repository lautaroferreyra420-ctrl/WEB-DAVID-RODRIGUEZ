from django.conf import settings


def whatsapp(request):
    return {'whatsapp_number': settings.WHATSAPP_NUMBER}
