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

    return max(0, round(nuevo_elo_a)), max(0, round(nuevo_elo_b))

def calcular_nuevo_elo_parejas(elo_jugadores, elo_rivales, resultado, k=32):
    """
    Calculates the new Elo rating for 2v2 matches.

    Parameters:
    - elo_jugadores: List of two Elo ratings (team members).
    - elo_rivales: List of two Elo ratings (opponents).
    - resultado: 1 if the team won, 0 if they lost.
    - k: K-factor (default 32, adjusts Elo change sensitivity).

    Returns:
    - New Elo ratings for both players in the team.
    """

    # Calculate average Elo for each team
    elo_equipo = sum(elo_jugadores) / 2
    elo_rivales = sum(elo_rivales) / 2

    # Expected win probability using the standard Elo formula
    expected_win_prob = 1 / (1 + 10 ** ((elo_rivales - elo_equipo) / 400))

    # Elo update formula
    nuevo_elo = [
        max(0, round(elo + k * (resultado - expected_win_prob)))
        for elo in elo_jugadores
    ]

    return nuevo_elo