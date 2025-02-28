from django.shortcuts import render

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Usuario, GuiñoteGame
import random
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt  # Disable CSRF protection for simplicity (not recommended for production)
def crear_partida(request):
    """
    Creates a new Guiñote match between two players.
    Expects a JSON request body with 'jugador1_id' and 'jugador2_id'.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            jugador1 = get_object_or_404(Usuario, id=data["jugador1_id"])
            jugador2 = get_object_or_404(Usuario, id=data["jugador2_id"])

            partida = GuiñoteGame.objects.create(
                jugador_1=jugador1,
                jugador_2=jugador2,
                turno_actual=jugador1  # First turn goes to player 1
            )
            barajar_cartas(partida)  # Shuffle and deal cards
            return JsonResponse({"message": "Partida creada", "partida_id": partida.id}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)


def barajar_cartas(partida):
    """
    Shuffles the deck, sets the triumph suit, and distributes cards.
    """
    baraja = [{'palo': palo, 'valor': valor} for palo in ['oros', 'copas', 'espadas', 'bastos']
              for valor in ['as', 'tres', 'rey', 'caballo', 'sota', 'siete', 'seis', 'cinco', 'cuatro', 'dos']]

    random.shuffle(baraja)

    partida.cartas_jugador_1 = baraja[:5]
    partida.cartas_jugador_2 = baraja[5:10]
    partida.mazo_restante = baraja[10:]
    partida.triunfo_palo = partida.mazo_restante[-1]['palo']
    partida.save()

@csrf_exempt
def obtener_estado_partida(request, partida_id):
    """
    Retrieves the current state of the match.
    """
    partida = get_object_or_404(GuiñoteGame, id=partida_id)
    
    estado = {
        "jugador_1": partida.jugador_1.nombre,
        "jugador_2": partida.jugador_2.nombre,
        "puntos_jugador_1": partida.puntos_jugador_1,
        "puntos_jugador_2": partida.puntos_jugador_2,
        "cartas_jugador_1": partida.cartas_jugador_1,
        "cartas_jugador_2": partida.cartas_jugador_2,
        "cartas_jugadas": partida.cartas_jugadas,
        "triunfo_palo": partida.triunfo_palo,
        "mazo_restante": len(partida.mazo_restante),
        "turno_actual": partida.turno_actual.nombre if partida.turno_actual else "N/A",
        "estado": partida.estado_partida,
    }
    
    return JsonResponse(estado)
