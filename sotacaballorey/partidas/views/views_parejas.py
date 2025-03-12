from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from partidas.models import Partida2v2
from usuarios.models import Usuario
from ..elo import calcular_nuevo_elo_parejas  # Assumed existing function


@csrf_exempt
def crear_partida(request):
    """
    Creates a new 2v2 match between four players.
    Expects a JSON request body with 'equipo_1_jugador_1', 'equipo_1_jugador_2',
    'equipo_2_jugador_1', and 'equipo_2_jugador_2'.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Get players
            equipo_1_jugador_1 = get_object_or_404(Usuario, id=data["equipo_1_jugador_1"])
            equipo_1_jugador_2 = get_object_or_404(Usuario, id=data["equipo_1_jugador_2"])
            equipo_2_jugador_1 = get_object_or_404(Usuario, id=data["equipo_2_jugador_1"])
            equipo_2_jugador_2 = get_object_or_404(Usuario, id=data["equipo_2_jugador_2"])

            # Create match
            partida = Partida2v2.objects.create(
                equipo_1_jugador_1=equipo_1_jugador_1,
                equipo_1_jugador_2=equipo_1_jugador_2,
                equipo_2_jugador_1=equipo_2_jugador_1,
                equipo_2_jugador_2=equipo_2_jugador_2,
                turno_actual=equipo_1_jugador_1  # First player in Team 1 starts
            )

            return JsonResponse({"message": "Partida 2v2 creada", "partida_id": partida.id}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
def obtener_estado_partida(request, partida_id):
    """
    Retrieves the current state of a 2v2 match.
    """
    partida = get_object_or_404(Partida2v2, id=partida_id)

    estado = {
        "equipo_1": [partida.equipo_1_jugador_1.nombre, partida.equipo_1_jugador_2.nombre],
        "equipo_2": [partida.equipo_2_jugador_1.nombre, partida.equipo_2_jugador_2.nombre],
        "puntos_equipo_1": partida.puntos_equipo_1,
        "puntos_equipo_2": partida.puntos_equipo_2,
        "cartas_jugadas": partida.cartas_jugadas,
        "triunfo_palo": partida.triunfo_palo,
        "mazo_restante": len(partida.mazo_restante),
        "turno_actual": partida.turno_actual.nombre if partida.turno_actual else "N/A",
        "estado": partida.estado_partida,
        "equipo_ganador": "Equipo 1" if partida.equipo_ganador == 1 else "Equipo 2" if partida.equipo_ganador == 2 else None
    }

    return JsonResponse(estado)


@csrf_exempt
def cambiar_estado_partida(request, partida_id):
    """
    Changes the state of a 2v2 match from 'EN_JUEGO' to 'FINALIZADO' and updates player stats.
    Requires an 'equipo_ganador' in the request.
    """
    if request.method == "POST":
        try:
            partida = get_object_or_404(Partida2v2, id=partida_id)
            data = json.loads(request.body)

            nuevo_estado = data.get("estado")
            equipo_ganador = data.get("equipo_ganador")

            # Validate match state transition
            if partida.estado_partida != "EN_JUEGO" or nuevo_estado != "FINALIZADO":
                return JsonResponse({"error": "Only ongoing matches can be set to FINALIZADO"}, status=400)

            # Validate winning team
            if equipo_ganador not in [1, 2]:
                return JsonResponse({"error": "Invalid winning team"}, status=400)

            # Determine winners and losers
            if equipo_ganador == 1:
                ganadores = [partida.equipo_1_jugador_1, partida.equipo_1_jugador_2]
                perdedores = [partida.equipo_2_jugador_1, partida.equipo_2_jugador_2]
            else:
                ganadores = [partida.equipo_2_jugador_1, partida.equipo_2_jugador_2]
                perdedores = [partida.equipo_1_jugador_1, partida.equipo_1_jugador_2]

            # Update stats using transaction
            with transaction.atomic():
                # Calculate new Elo for winners
                nuevos_elo_ganadores = calcular_nuevo_elo_parejas(
                    [ganadores[0].elo_parejas, ganadores[1].elo_parejas],
                    [perdedores[0].elo_parejas, perdedores[1].elo_parejas],
                    1
                )

                # Assign new Elo values to winners
                for i, ganador in enumerate(ganadores):
                    ganador.victorias += 1
                    ganador.racha_victorias += 1
                    ganador.elo_parejas = nuevos_elo_ganadores[i]

                    if ganador.racha_victorias > ganador.mayor_racha_victorias:
                        ganador.mayor_racha_victorias = ganador.racha_victorias
                    ganador.save()

                # Calculate new Elo for losers
                nuevos_elo_perdedores = calcular_nuevo_elo_parejas(
                    [perdedores[0].elo_parejas, perdedores[1].elo_parejas],
                    [ganadores[0].elo_parejas, ganadores[1].elo_parejas],
                    0
                )

                # Assign new Elo values to losers
                for i, perdedor in enumerate(perdedores):
                    perdedor.derrotas += 1
                    perdedor.racha_victorias = 0  # Reset on loss
                    perdedor.elo_parejas = nuevos_elo_perdedores[i]
                    perdedor.save()

                # Update match status
                partida.estado_partida = "FINALIZADO"
                partida.equipo_ganador = equipo_ganador
                partida.save()

            return JsonResponse({
                "message": "Partida 2v2 finalizada",
                "estado": partida.estado_partida,
                "equipo_ganador": f"Equipo {equipo_ganador}",
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)
