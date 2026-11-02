"""Errores de dominio de Atempo."""


class ErrorDeDominio(ValueError):
    """Violación de una regla de negocio."""


class ActividadIncompleta(ErrorDeDominio):
    """RN-01: toda actividad exige nombre, fecha límite y horas estimadas."""


class HorasInvalidas(ErrorDeDominio):
    """RN-02: las horas deben estar entre 0 y 24."""


class ErrorNoEncontrado(ErrorDeDominio):
    """El recurso pedido no existe (la API responde 404)."""

    def __init__(self, recurso: str):
        super().__init__(f"La {recurso} no existe.")
