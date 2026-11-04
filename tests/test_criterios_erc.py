"""Pruebas de aceptación que citan los casos de prueba PA-xx del DDS y los CA-xx del ERS."""
import time
import unittest
from datetime import date

from atempo.dominio.calculadora import CalculadoraDeCarga, porcentaje_para_mostrar
from atempo.dominio.modelos import Actividad, Nivel
from atempo.servicios.dashboard import Dashboard
from atempo.datos.sesiones import GestorDeSesiones
from atempo.web import crear_app
from atempo.datos.sesiones import SesionDemo

DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
F = date(2026, 11, 10)


def sesion_con(pendientes, disponibles):
    s = SesionDemo(hoy=date(2026, 11, 1))
    for a in list(s.actividades()):
        s.eliminar_actividad(a.id)
    s.guardar_disponibilidad({d: disponibles / 7 for d in DIAS})
    if pendientes:
        s.guardar_actividad({"nombre": "A", "fecha_limite": "2026-11-10",
                             "horas_estimadas": pendientes, "materia_id": 1})
    return s


class TestPA(unittest.TestCase):
    def test_pa05_pa06_pa07_niveles(self):
        casos = [(17, 20, Nivel.ALTA), (12, 20, Nivel.MEDIA), (9, 20, Nivel.BAJA),
                 (10, 20, Nivel.MEDIA), (16, 20, Nivel.MEDIA), (16.2, 20, Nivel.ALTA)]
        for pend, disp, esperado in casos:
            r = CalculadoraDeCarga().calcular([Actividad(1, "A", F, pend, False, 1)], disp)
            self.assertEqual(r.nivel, esperado, (pend, disp))

    def test_pa05_texto(self):
        self.assertEqual(Dashboard(sesion_con(17, 20)).mostrar(), "Carga Alta (85%)")

    def test_pa09_valores_del_ers(self):
        s = sesion_con(17, 20)
        extra = s.guardar_actividad(
            {"nombre": "B", "fecha_limite": "2026-11-10", "horas_estimadas": 3, "materia_id": 1})
        self.assertEqual(Dashboard(s).mostrar(), "Carga Alta (100%)")   # 20/20
        s.cambiar_estado(extra.id, True)
        self.assertEqual(Dashboard(s).mostrar(), "Carga Alta (85%)")    # 17/20

    def test_pa13_porcentaje_no_contradice(self):
        r = CalculadoraDeCarga().calcular([Actividad(1, "A", F, 16.1, False, 1)], 20)
        self.assertEqual(r.nivel, Nivel.ALTA)
        self.assertEqual(porcentaje_para_mostrar(r.nivel, r.porcentaje), 81)

    def test_pa10_sin_actividades(self):
        self.assertEqual(Dashboard(sesion_con(0, 20)).mostrar(), "Aún no tienes actividades pendientes")

    def test_pa01_pa02_mensajes(self):
        c = crear_app(GestorDeSesiones()).test_client()
        r = c.post("/api/v1/materias", json={"nombre": "  "})
        self.assertEqual(r.get_json()["error"], "El nombre de la materia es obligatorio")
        r = c.post("/api/v1/actividades", json={"nombre": "X", "materia_id": 1, "horas_estimadas": 2})
        self.assertIn("fecha de entrega", r.get_json()["error"])
        r = c.post("/api/v1/actividades", json={"nombre": "X", "materia_id": 1, "fecha_limite": "2026-11-10"})
        self.assertIn("horas estimadas", r.get_json()["error"])

    def test_pa03_horas_fuera_de_rango(self):
        c = crear_app(GestorDeSesiones()).test_client()
        cuerpo = {d: 1 for d in DIAS}
        cuerpo["Lunes"] = 25
        self.assertEqual(c.put("/api/v1/disponibilidad", json=cuerpo).get_json()["error"],
                         "Las horas deben estar entre 0 y 24.")

    def test_pa04_total_semanal(self):
        s = SesionDemo()
        s.guardar_disponibilidad({"Lunes": 2, "Martes": 2, "Miércoles": 2, "Jueves": 2, "Viernes": 2, "Sábado": 4})
        self.assertEqual(s.horas_disponibles(), 14)

    def test_pa12_rendimiento_50_actividades(self):
        c = crear_app(GestorDeSesiones()).test_client()
        for i in range(50):
            c.post("/api/v1/actividades", json={"nombre": f"Act {i}", "materia_id": 1,
                                                "fecha_limite": "2026-11-20", "horas_estimadas": 1})
        tiempos = []
        for _ in range(5):
            t = time.perf_counter()
            c.get("/api/v1/estado")
            tiempos.append(time.perf_counter() - t)
        self.assertLess(max(tiempos), 3.0)


if __name__ == "__main__":
    unittest.main()
