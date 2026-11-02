"""Recomendaciones ordenadas por fecha (RN-05)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .modelos import Actividad, Nivel

DIAS_URGENTE = 3


@dataclass(frozen=True)
class Recomendacion:
    actividad: Actividad
    dias_restantes: int
    resaltada: bool


def recomendar(actividades: Iterable[Actividad], hoy: date,
               nivel: Nivel | None) -> list[Recomendacion]:
    pend = sorted((a for a in actividades if not a.completada),
                  key=lambda a: (a.fecha_limite, a.id))
    res = []
    for a in pend:
        dias = (a.fecha_limite - hoy).days
        res.append(Recomendacion(a, dias, nivel is Nivel.ALTA and dias <= DIAS_URGENTE))
    return res
