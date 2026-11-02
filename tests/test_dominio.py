import unittest
from datetime import date

from atempo.dominio.calculadora import CalculadoraDeCarga, porcentaje_para_mostrar
from atempo.dominio.errores import ActividadIncompleta, HorasInvalidas
from atempo.dominio.modelos import Actividad, Nivel, validar_horas
from atempo.dominio.priorizador import recomendar
from atempo.dominio.semana import fin_de_semana, inicio_de_semana

F = date(2026, 11, 10)


def act(i, h, done=False, f=F):
    return Actividad(i, f"A{i}", f, h, done, 1)


class TestCalculadora(unittest.TestCase):
    def setUp(self):
        self.c = CalculadoraDeCarga()

    def nivel(self, pend, disp):
        return self.c.calcular([act(1, pend)], disp).nivel

    def test_limites(self):
        self.assertEqual(self.nivel(49.9, 100), Nivel.BAJA)
        self.assertEqual(self.nivel(50, 100), Nivel.MEDIA)
        self.assertEqual(self.nivel(80, 100), Nivel.MEDIA)
        self.assertEqual(self.nivel(80.5, 100), Nivel.ALTA)

    def test_completada_no_cuenta(self):
        r = self.c.calcular([act(1, 10, True), act(2, 5)], 10)
        self.assertEqual(r.horas_pendientes, 5)
        self.assertEqual(r.nivel, Nivel.MEDIA)

    def test_sin_disponibilidad(self):
        r = self.c.calcular([act(1, 5)], 0)
        self.assertIsNone(r.nivel)
        self.assertIsNone(r.porcentaje)

    def test_sin_pendientes(self):
        self.assertEqual(self.c.calcular([], 10).porcentaje, 0)

    def test_bug001_porcentaje_coherente(self):
        p = 0.0
        while p <= 200:
            n = CalculadoraDeCarga._clasificar(p)
            m = porcentaje_para_mostrar(n, p)
            if n is Nivel.ALTA:
                self.assertGreater(m, 80, p)
            elif n is Nivel.BAJA:
                self.assertLess(m, 50, p)
            else:
                self.assertTrue(50 <= m <= 80, p)
            p = round(p + 0.01, 2)


class TestModelos(unittest.TestCase):
    def test_rn01(self):
        with self.assertRaises(ActividadIncompleta):
            Actividad(1, " ", F, 2, False, 1)
        with self.assertRaises(ActividadIncompleta):
            Actividad(1, "x", None, 2, False, 1)
        with self.assertRaises(ActividadIncompleta):
            Actividad(1, "x", F, None, False, 1)

    def test_rn01_materia_obligatoria(self):
        with self.assertRaises(ActividadIncompleta):
            Actividad(1, "x", F, 2)

    def test_horas_estimadas_positivas(self):
        with self.assertRaises(HorasInvalidas):
            Actividad(1, "x", F, 0, False, 1)

    def test_rn02(self):
        self.assertEqual(validar_horas(0), 0.0)
        self.assertEqual(validar_horas(24), 24.0)
        for malo in (-1, 25, "3", True, None):
            with self.assertRaises(HorasInvalidas):
                validar_horas(malo)

    def test_inmutable(self):
        a = act(1, 3)
        b = a.marcar_completada()
        self.assertFalse(a.completada)
        self.assertTrue(b.completada)
        self.assertFalse(b.reabrir().completada)


class TestPriorizador(unittest.TestCase):
    def test_orden_y_resaltado(self):
        hoy = date(2026, 11, 1)
        a = [act(1, 2, f=date(2026, 11, 10)), act(2, 2, f=date(2026, 11, 3)),
             act(3, 2, True, f=date(2026, 11, 2))]
        r = recomendar(a, hoy, Nivel.ALTA)
        self.assertEqual([x.actividad.id for x in r], [2, 1])
        self.assertTrue(r[0].resaltada)
        self.assertFalse(r[1].resaltada)
        self.assertFalse(recomendar(a, hoy, Nivel.MEDIA)[0].resaltada)


class TestSemana(unittest.TestCase):
    def test_lunes_domingo(self):
        d = date(2026, 11, 1)  # domingo
        self.assertEqual(inicio_de_semana(d), date(2026, 10, 26))
        self.assertEqual(fin_de_semana(d), d)


if __name__ == "__main__":
    unittest.main()
