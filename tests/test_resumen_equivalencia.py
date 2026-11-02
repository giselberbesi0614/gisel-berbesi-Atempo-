"""Prueba de caracterización: Dashboard.resumen() debe devolver exactamente lo mismo antes y después de refactorizar.
Los resultados esperados (tests/golden_resumen.json) se capturaron con la versión anterior al refactor."""
import json
import os
import unittest
from datetime import date

from atempo.datos.sesiones import SesionDemo
from atempo.servicios.dashboard import Dashboard

DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
HOY = date(2026, 11, 1)
GOLDEN = os.path.join(os.path.dirname(__file__), "golden_resumen.json")


def base(horas_dia=None):
    s = SesionDemo(hoy=HOY)
    if horas_dia is not None:
        s.guardar_disponibilidad({d: horas_dia for d in DIAS})
    return s


def sin_actividades(horas_dia):
    s = base(horas_dia)
    for a in list(s.actividades()):
        s.eliminar_actividad(a.id)
    return s


def escenarios():
    e = {}
    e["demo"] = base()
    e["sin_actividades_con_horas"] = sin_actividades(3)
    e["sin_horas"] = sin_actividades(0)
    s = base(1)                                           # carga alta
    e["alta"] = s
    s = base(10)                                          # carga baja
    e["baja"] = s
    s = base()
    for a in list(s.actividades()):
        s.cambiar_estado(a.id, True)                      # todo completado
    e["todo_completado"] = s
    s = base(2)
    s.guardar_materia({"nombre": "Sin actividades", "docente": "", "color": "#123456"})
    e["materia_sin_actividades"] = s
    s = sin_actividades(2)
    m = s.guardar_materia({"nombre": "Temporal", "docente": "", "color": "#654321"})
    s.guardar_actividad({"nombre": "Vencida", "fecha_limite": "2026-10-20",
                         "horas_estimadas": 2, "materia_id": m.id})
    e["vencida"] = s
    return e


def calcular():
    return {k: Dashboard(s, hoy=HOY).resumen() for k, s in escenarios().items()}


class TestEquivalencia(unittest.TestCase):
    def test_resumen_identico_al_de_referencia(self):
        esperado = json.load(open(GOLDEN, encoding="utf-8"))
        actual = json.loads(json.dumps(calcular()))
        self.assertEqual(actual.keys(), esperado.keys())
        for k in esperado:
            with self.subTest(k):
                self.assertEqual(actual[k], esperado[k])


if __name__ == "__main__":
    unittest.main()
