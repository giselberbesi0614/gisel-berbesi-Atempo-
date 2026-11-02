"""Modelos del dominio (inmutables)."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum

from .errores import ActividadIncompleta, HorasInvalidas


class Nivel(str, Enum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"


def validar_horas(horas) -> float:
    """RN-02: número entre 0 y 24 (0 permitido)."""
    if isinstance(horas, bool) or not isinstance(horas, (int, float)):
        raise HorasInvalidas("Las horas deben ser un número.")
    if horas < 0 or horas > 24:
        raise HorasInvalidas("Las horas deben estar entre 0 y 24.")
    return float(horas)


@dataclass(frozen=True)
class Actividad:
    id: int
    nombre: str
    fecha_limite: date
    horas_estimadas: float
    completada: bool = False
    materia_id: int = 0

    def __post_init__(self):
        if not self.nombre or not self.nombre.strip():
            raise ActividadIncompleta("Falta el campo: nombre de la actividad.")
        if not self.materia_id:
            raise ActividadIncompleta("Falta el campo: materia.")
        if not isinstance(self.fecha_limite, date):
            raise ActividadIncompleta("Falta el campo: fecha de entrega.")
        if self.horas_estimadas is None:
            raise ActividadIncompleta("Falta el campo: horas estimadas.")
        if isinstance(self.horas_estimadas, bool) or not isinstance(
                self.horas_estimadas, (int, float)) or self.horas_estimadas <= 0:
            raise HorasInvalidas("Las horas estimadas deben ser mayores que 0.")

    def marcar_completada(self) -> "Actividad":
        return replace(self, completada=True)

    def reabrir(self) -> "Actividad":
        return replace(self, completada=False)


@dataclass(frozen=True)
class ResultadoCarga:
    nivel: Nivel | None
    porcentaje: float | None
    horas_pendientes: float
    horas_disponibles: float


@dataclass(frozen=True)
class Materia:
    id: int
    nombre: str
    docente: str = ""
    color: str = "#6656D9"

    def __post_init__(self):
        if not self.nombre or not self.nombre.strip():
            raise ActividadIncompleta("El nombre de la materia es obligatorio")


DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
