"""Cálculo de la carga académica (RN-03, RN-04)."""
from __future__ import annotations

import math
from typing import Iterable

from .modelos import Actividad, Nivel, ResultadoCarga

UMBRAL_MEDIA = 50   # Baja: < 50
UMBRAL_ALTA = 80    # Media: 50..80 inclusive; Alta: > 80


class CalculadoraDeCarga:
    """Solo calcula; no genera textos ni accede a datos."""

    def calcular(self, actividades: Iterable[Actividad],
                 horas_disponibles: float) -> ResultadoCarga:
        pendientes = sum(a.horas_estimadas for a in actividades
                         if not a.completada)           # RN-04
        if not horas_disponibles or horas_disponibles <= 0:
            return ResultadoCarga(None, None, pendientes, horas_disponibles or 0)
        porcentaje = pendientes / horas_disponibles * 100
        return ResultadoCarga(self._clasificar(porcentaje), porcentaje,
                              pendientes, horas_disponibles)

    @staticmethod
    def _clasificar(p: float) -> Nivel:
        if p < UMBRAL_MEDIA:
            return Nivel.BAJA
        if p <= UMBRAL_ALTA:
            return Nivel.MEDIA
        return Nivel.ALTA


def porcentaje_para_mostrar(nivel: Nivel, p: float) -> int:
    """Corrige BUG-001: el entero mostrado nunca contradice el nivel."""
    r = math.floor(p + 0.5)
    if nivel is Nivel.ALTA:
        return max(r, UMBRAL_ALTA + 1)
    if nivel is Nivel.BAJA:
        return min(r, UMBRAL_MEDIA - 1)
    return min(max(r, UMBRAL_MEDIA), UMBRAL_ALTA)
