"""Fallo controlado, idempotencia y concurrencia sobre SesionDemo (referidas en II-03 y II-04)."""
import threading
import unittest
from datetime import date

from atempo.datos.sesiones import SesionDemo
from atempo.dominio.errores import ErrorDeDominio

ACT = {"nombre": "Taller", "fecha_limite": "2026-11-10", "horas_estimadas": 2, "materia_id": 1}


class TestRobustez(unittest.TestCase):
    def setUp(self):
        self.s = SesionDemo(hoy=date(2026, 11, 1))

    def test_rechazo_no_cambia_el_estado(self):
        antes = (self.s.actividades(), self.s.horas_disponibles())
        with self.assertRaises(ErrorDeDominio):
            self.s.guardar_actividad({**ACT, "nombre": ""})
        with self.assertRaises(ErrorDeDominio):
            self.s.guardar_disponibilidad({"Lunes": 30})
        self.assertEqual(antes, (self.s.actividades(), self.s.horas_disponibles()))

    def test_disponibilidad_invalida_no_guarda_parcial(self):
        base = self.s.disponibilidad()
        datos = dict(base)
        datos["Domingo"] = -1
        with self.assertRaises(ErrorDeDominio):
            self.s.guardar_disponibilidad(datos)
        self.assertEqual(self.s.disponibilidad(), base)

    def test_completar_es_idempotente(self):
        a = self.s.guardar_actividad(ACT)
        primera = self.s.cambiar_estado(a.id, True)
        segunda = self.s.cambiar_estado(a.id, True)
        self.assertEqual(primera, segunda)
        self.assertEqual(sum(x.completada for x in self.s.actividades() if x.id == a.id), 1)

    def test_concurrencia_sin_ids_duplicados_ni_perdidas(self):
        n_hilos, por_hilo = 8, 25
        errores = []

        def trabajo():
            try:
                for _ in range(por_hilo):
                    self.s.guardar_actividad(ACT)
            except Exception as e:  # pragma: no cover
                errores.append(e)

        hilos = [threading.Thread(target=trabajo) for _ in range(n_hilos)]
        [h.start() for h in hilos]
        [h.join() for h in hilos]
        ids = [a.id for a in self.s.actividades()]
        self.assertEqual(errores, [])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 5 + n_hilos * por_hilo)

    def test_concurrencia_completar_y_borrar(self):
        a = self.s.guardar_actividad(ACT)
        resultados = []

        def completar():
            try:
                self.s.cambiar_estado(a.id, True)
                resultados.append("ok")
            except ErrorDeDominio:
                resultados.append("no_existe")

        def borrar():
            try:
                self.s.eliminar_actividad(a.id)
                resultados.append("borrada")
            except ErrorDeDominio:
                resultados.append("no_existe")

        hilos = [threading.Thread(target=f) for f in (completar, borrar) * 10]
        [h.start() for h in hilos]
        [h.join() for h in hilos]
        self.assertEqual(len(resultados), 20)
        self.assertEqual(resultados.count("borrada"), 1)       # solo una eliminación puede ocurrir
        self.assertNotIn(a.id, [x.id for x in self.s.actividades()])


if __name__ == "__main__":
    unittest.main()
