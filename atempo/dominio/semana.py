"""RN-07: semana de lunes a domingo."""
from datetime import date, timedelta


def inicio_de_semana(d: date) -> date:
    return d - timedelta(days=d.weekday())


def fin_de_semana(d: date) -> date:
    return inicio_de_semana(d) + timedelta(days=6)
