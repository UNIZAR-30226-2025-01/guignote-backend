from django.core.management.base import BaseCommand
from django.utils.timezone import now
from partidas.models import Partida
from datetime import timedelta

class Command(BaseCommand):
    help = 'Elimina partidas finalizadas con más de 10 minutos de antigüedad'

    def handle(self, *args, **kwargs):
        expiracion = now() - timedelta(minutes=10)
        partidas = Partida.objects.filter(estado='terminada', fecha_fin__lt=expiracion)
        count = partidas.count()
        partidas.delete()
        self.stdout.write(f'Eliminadas {count} partidas finalizadas')