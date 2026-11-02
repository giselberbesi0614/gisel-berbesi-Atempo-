"""Pruebas de integración: la API real cumple docs/openapi.yaml.
Base de datos efímera (SQLite en memoria); no hay APIs externas que simular."""
import os
import unittest

import jsonschema
import yaml

from atempo.datos.sqlite import Repositorio
from atempo.web import crear_app

RUTA = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.yaml")
MATERIA = {"nombre": "Redes", "docente": "Ana", "color": "#112233"}
ACTIVIDAD = {"nombre": "Taller", "fecha_limite": "2026-11-10", "horas_estimadas": 2, "materia_id": 1}


def _anular_nullable(o):
    """jsonschema no entiende «nullable» de OpenAPI 3.0: se traduce a un tipo doble."""
    if isinstance(o, dict):
        if o.get("nullable") and "type" in o:
            o["type"] = [o["type"], "null"]
        for v in o.values():
            _anular_nullable(v)
    elif isinstance(o, list):
        for v in o:
            _anular_nullable(v)


class TestContrato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RUTA, encoding="utf-8") as f:
            cls.spec = yaml.safe_load(f)
        _anular_nullable(cls.spec)

    def setUp(self):
        self.repo = Repositorio(":memory:")           # efímera: desaparece al terminar la prueba
        self.addCleanup(self.repo.cerrar)
        self.c = crear_app(self.repo).test_client()

    def cumple(self, resp, ruta, metodo, codigo):
        self.assertEqual(resp.status_code, int(codigo))
        r = self.spec["paths"][ruta][metodo]["responses"][codigo]
        if "$ref" in r:
            r = self.spec["components"]["responses"][r["$ref"].split("/")[-1]]
        esquema = {**r["content"]["application/json"]["schema"], "components": self.spec["components"]}
        jsonschema.validate(resp.get_json(), esquema, resolver=jsonschema.RefResolver.from_schema(esquema))

    def test_get_estado(self):
        self.cumple(self.c.get("/api/v1/estado"), "/api/v1/estado", "get", "200")

    def test_post_materia_201_y_400(self):
        self.cumple(self.c.post("/api/v1/materias", json=MATERIA), "/api/v1/materias", "post", "201")
        self.cumple(self.c.post("/api/v1/materias", json={}), "/api/v1/materias", "post", "400")

    def test_put_materia(self):
        r = self.c.put("/api/v1/materias/1", json={"nombre": "Redes II"})
        self.cumple(r, "/api/v1/materias/{id}", "put", "200")

    def test_delete_materia_inexistente_404(self):
        self.cumple(self.c.delete("/api/v1/materias/999"), "/api/v1/materias/{id}", "delete", "404")

    def test_post_actividad_201_y_400(self):
        self.cumple(self.c.post("/api/v1/actividades", json=ACTIVIDAD), "/api/v1/actividades", "post", "201")
        self.cumple(self.c.post("/api/v1/actividades", json={"nombre": "x"}), "/api/v1/actividades", "post", "400")

    def test_put_actividad(self):
        self.cumple(self.c.put("/api/v1/actividades/1", json=ACTIVIDAD), "/api/v1/actividades/{id}", "put", "200")

    def test_patch_completada(self):
        r = self.c.patch("/api/v1/actividades/1/completada", json={"completada": True})
        self.cumple(r, "/api/v1/actividades/{id}/completada", "patch", "200")

    def test_delete_actividad_inexistente_404(self):
        self.cumple(self.c.delete("/api/v1/actividades/999"), "/api/v1/actividades/{id}", "delete", "404")

    def test_put_disponibilidad(self):
        self.cumple(self.c.put("/api/v1/disponibilidad", json={"Lunes": 3}), "/api/v1/disponibilidad", "put", "200")

    def test_reiniciar(self):
        self.cumple(self.c.post("/api/v1/reiniciar"), "/api/v1/reiniciar", "post", "200")

    def test_salud(self):
        self.cumple(self.c.get("/salud"), "/salud", "get", "200")

    def test_todas_las_operaciones_declaran_seguridad(self):
        for ruta, ops in self.spec["paths"].items():
            for metodo, op in ops.items():
                if metodo in ("get", "post", "put", "patch", "delete"):
                    self.assertIn("security", op, f"{metodo.upper()} {ruta}")

    def test_aislamiento_no_toca_base_real(self):
        """La regla de oro: el entorno no puede apuntar las pruebas a una base de desarrollo real."""
        self.assertEqual(self.repo.con.execute("PRAGMA database_list").fetchone()[2], "")
