"""Caso de uso: resumen del tablero. Recibe la fuente por inyección (DIP)."""
from __future__ import annotations

from datetime import date

from ..datos.fuente import FuenteDeDatos
from ..dominio.calculadora import CalculadoraDeCarga, porcentaje_para_mostrar
from ..dominio.modelos import Nivel
from ..dominio.priorizador import recomendar
from ..dominio.semana import fin_de_semana, inicio_de_semana


class Dashboard:
    def __init__(self, fuente: FuenteDeDatos, calculadora: CalculadoraDeCarga | None = None,
                 hoy: date | None = None):
        self.fuente = fuente
        self.calc = calculadora or CalculadoraDeCarga()
        self.hoy = hoy or date.today()

    def mostrar(self) -> str:
        r = self.calc.calcular(self.fuente.actividades(), self.fuente.horas_disponibles())
        if r.nivel is None:
            return "Registra tus horas disponibles para calcular tu carga"
        if r.horas_pendientes == 0:
            return "Aún no tienes actividades pendientes"       # corrige BUG-002
        return f"Carga {r.nivel.value} ({porcentaje_para_mostrar(r.nivel, r.porcentaje)}%)"

    def resumen(self) -> dict:
        acts = self.fuente.actividades()
        materias = {m.id: m for m in self.fuente.materias()}
        r = self.calc.calcular(acts, self.fuente.horas_disponibles())
        return {
            "hoy": self.hoy.isoformat(),
            "semana": self._semana(),
            "carga": self._carga(r),
            "progreso": self._progreso(acts),
            "recomendaciones": self._recomendaciones(acts, materias, r.nivel),
            "horas_por_materia": self._horas_por_materia(acts, materias),
        }

    def _semana(self) -> dict:
        return {"inicio": inicio_de_semana(self.hoy).isoformat(),
                "fin": fin_de_semana(self.hoy).isoformat()}

    def _carga(self, r) -> dict:
        nivel = r.nivel
        return {
            "nivel": nivel.value if nivel else None,
            "porcentaje": porcentaje_para_mostrar(nivel, r.porcentaje) if nivel else None,
            "horas_pendientes": r.horas_pendientes,
            "horas_disponibles": r.horas_disponibles,
            "mensaje": self.mostrar(),
            "alta": nivel is Nivel.ALTA,
        }

    @staticmethod
    def _progreso(acts) -> dict:
        hechas = sum(1 for a in acts if a.completada)
        return {"completadas": hechas, "pendientes": len(acts) - hechas,
                "porcentaje": round(hechas / len(acts) * 100) if acts else 0}

    def _recomendaciones(self, acts, materias, nivel) -> list:
        def materia(x):
            m = materias.get(x.actividad.materia_id)
            return m.nombre if m else ""
        return [{"actividad_id": x.actividad.id, "nombre": x.actividad.nombre,
                 "materia": materia(x),
                 "fecha_limite": x.actividad.fecha_limite.isoformat(),
                 "dias_restantes": x.dias_restantes,
                 "horas": x.actividad.horas_estimadas, "resaltada": x.resaltada}
                for x in recomendar(acts, self.hoy, nivel)]

    @staticmethod
    def _horas_por_materia(acts, materias) -> list:
        horas = {}
        for a in acts:
            horas[a.materia_id] = horas.get(a.materia_id, 0) + a.horas_estimadas
        return [{"materia_id": m.id, "nombre": m.nombre, "color": m.color,
                 "horas": horas.get(m.id, 0)} for m in materias.values()]
