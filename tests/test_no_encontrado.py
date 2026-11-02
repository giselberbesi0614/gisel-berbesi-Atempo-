"""DEF-06 (TDD): un recurso que no existe responde 404, no 400 (Richardson, nivel 2)."""
import unittest

from atempo.datos.sesiones import GestorDeSesiones
from atempo.datos.sqlite import Repositorio
from atempo.web import crear_app

ACT = {"nombre": "X", "fecha_limite": "2026-11-10", "horas_estimadas": 2, "materia_id": 1}


class TestNoEncontrado(unittest.TestCase):
    def fuente(self):
        return GestorDeSesiones()

    def setUp(self):
        self.c = crear_app(self.fuente()).test_client()

    def casos(self):
        return [
            ("put", "/api/v1/materias/999", {"nombre": "X"}, "La materia no existe."),
            ("delete", "/api/v1/materias/999", None, "La materia no existe."),
            ("put", "/api/v1/actividades/999", ACT, "La actividad no existe."),
            ("patch", "/api/v1/actividades/999/completada", {"completada": True}, "La actividad no existe."),
            ("delete", "/api/v1/actividades/999", None, "La actividad no existe."),
        ]

    def test_inexistente_responde_404(self):
        for metodo, url, cuerpo, msg in self.casos():
            with self.subTest(f"{metodo.upper()} {url}"):
                r = getattr(self.c, metodo)(url, json=cuerpo)
                self.assertEqual(r.status_code, 404)
                self.assertEqual(r.get_json(), {"error": msg})

    def test_dato_invalido_sigue_siendo_400(self):
        self.assertEqual(self.c.post("/api/v1/materias", json={}).status_code, 400)
        self.assertEqual(self.c.post("/api/v1/actividades", json={"nombre": "x"}).status_code, 400)


class TestNoEncontradoSQLite(TestNoEncontrado):
    def fuente(self):
        r = Repositorio(":memory:")
        self.addCleanup(r.cerrar)
        return r
