import math

def calcular_nuevo_elo(rating_a, rating_b, resultado_a, k=32):
    """
    Calcula las nuevas puntuaciones Elo después de un partido.

    :param rating_a: Elo actual del jugador A
    :param rating_b: Elo actual del jugador B
    :param resultado_a: 1 si A gana, 0.5 si empate, 0 si A pierde
    :param k: Factor de ajuste (32 por defecto)
    :return: (nuevo_elo_A, nuevo_elo_B)
    """
    # Calcular la probabilidad esperada
    expectativa_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expectativa_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))

    # Calcular nuevo Elo
    nuevo_elo_a = rating_a + k * (resultado_a - expectativa_a)
    nuevo_elo_b = rating_b + k * ((1 - resultado_a) - expectativa_b)

    return round(nuevo_elo_a), round(nuevo_elo_b)
