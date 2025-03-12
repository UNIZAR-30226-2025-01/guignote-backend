import logging
import json
import random
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from partidas.models import Partida  # Import Partida (Match Object) from partidas app
from usuarios.models import Usuario  # Import Usuario (User Object) from usuarios app
from ..elo import calcular_nuevo_elo  # Import Elo calculation function


# Setup logger
logger = logging.getLogger(__name__)

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

            partida = Partida.objects.create(
                jugador_1=jugador1,
                jugador_2=jugador2,
                turno_actual=jugador1  # First turn goes to player 1
            )
            barajar_cartas(partida)  # Shuffle and deal cards

            logger.info(f"New match created: {partida.id} between {jugador1.nombre} and {jugador2.nombre}")

            return JsonResponse({"message": "Partida creada", "partida_id": partida.id}, status=201)

        except json.JSONDecodeError:
            logger.error("Invalid JSON format in request")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Error creating match: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    logger.warning("Invalid request method for crear_partida")
    return JsonResponse({"error": "Método no permitido"}, status=405)


def barajar_cartas(partida):
    """
    Shuffles the deck, sets the triumph suit, and distributes cards.
    """
    try:
        baraja = [{'palo': palo, 'valor': valor} for palo in ['oros', 'copas', 'espadas', 'bastos']
                  for valor in ['as', 'tres', 'rey', 'caballo', 'sota', 'siete', 'seis', 'cinco', 'cuatro', 'dos']]

        random.shuffle(baraja)

        partida.cartas_jugador_1 = baraja[:5]
        partida.cartas_jugador_2 = baraja[5:10]
        partida.mazo_restante = baraja[10:]
        partida.triunfo_palo = partida.mazo_restante[-1]['palo']
        partida.save()

        logger.info(f"Cards shuffled for match {partida.id}, triumph: {partida.triunfo_palo}")
    
    except Exception as e:
        logger.error(f"Error shuffling cards for match {partida.id}: {str(e)}")


@csrf_exempt
def obtener_estado_partida(request, partida_id):
    """
    Retrieves the current state of the match.
    """
    try:
        partida = get_object_or_404(Partida, id=partida_id)

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

        logger.info(f"Match {partida.id} state retrieved successfully")
        return JsonResponse(estado)

    except Partida.DoesNotExist:
        logger.warning(f"Match {partida_id} not found")
        return JsonResponse({"error": "Match not found"}, status=404)
    except Exception as e:
        logger.error(f"Error retrieving match {partida_id} state: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching match state"}, status=500)


@csrf_exempt
def cambiar_estado_partida(request, partida_id):
    """
    Handles a POST request to change the match state from 'EN_JUEGO' to 'FINALIZADO' 
    and updates player stats. Expects a JSON request body with 'ganador_id'.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        # Parse request body
        data = json.loads(request.body)
        nuevo_estado = data.get("estado")
        ganador_id = data.get("ganador_id")

        # Validate required fields
        if nuevo_estado is None or ganador_id is None:
            return JsonResponse({"error": "Missing required fields: 'estado' or 'ganador_id'"}, status=400)

        # Validate match existence
        partida = get_object_or_404(Partida, id=partida_id)

        # Validate state transition
        if partida.estado_partida != "EN_JUEGO" or nuevo_estado != "FINALIZADO":
            return JsonResponse({"error": "Only ongoing matches can be set to FINALIZADO"}, status=400)

        # Validate winner
        ganador = get_object_or_404(Usuario, id=ganador_id)
        if ganador not in [partida.jugador_1, partida.jugador_2]:
            return JsonResponse({"error": "Invalid winner ID"}, status=400)

        # Determine loser
        perdedor = partida.jugador_1 if ganador != partida.jugador_1 else partida.jugador_2

        # Update player stats
        ganador.victorias += 1
        ganador.racha_victorias += 1
        if ganador.racha_victorias > ganador.mayor_racha_victorias:
            ganador.mayor_racha_victorias = ganador.racha_victorias

        perdedor.derrotas += 1
        perdedor.racha_victorias = 0  # Reset loser’s streak
        
        # Calcular nuevo Elo
        nuevo_elo_ganador, nuevo_elo_perdedor = calcular_nuevo_elo(
            ganador.elo, perdedor.elo, resultado_a=1
        )

        # Guardar nuevas puntuaciones
        ganador.elo = nuevo_elo_ganador
        perdedor.elo = nuevo_elo_perdedor

        # Save changes
        ganador.save()
        perdedor.save()

        # Update match status
        partida.estado_partida = "FINALIZADO"
        partida.ganador = ganador
        partida.save()

        return JsonResponse({
            "mensaje": "Fin de la partida",
            "estado": partida.estado_partida,
            "ganador": ganador.nombre,
            "racha": ganador.racha_victorias,
            "mayor_racha": ganador.mayor_racha_victorias
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Partida.DoesNotExist:
        return JsonResponse({"error": "Match not found"}, status=404)
    except Usuario.DoesNotExist:
        return JsonResponse({"error": "Winner not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)