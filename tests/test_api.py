import unittest

from atempo.datos.sesiones import GestorDeSesiones
from atempo.web import crear_app


class TestApi(unittest.TestCase):
    def setUp(self):
        self.c = crear_app(GestorDeSesiones()).test_client()

    def estado(self):
        return self.c.get("/api/v1/estado").get_json()

    def test_estado_inicial_media(self):
        e = self.estado()
        self.assertEqual(len(e["materias"]), 4)
        self.assertEqual(e["resumen"]["carga"]["nivel"], "Media")   # 14h / 19h = 74%
        self.assertEqual(e["resumen"]["carga"]["porcentaje"], 74)

    def test_crear_actividad_y_completar(self):
        r = self.c.post("/api/v1/actividades", json={
            "nombre": "Taller", "fecha_limite": "2026-12-01",
            "horas_estimadas": 3, "materia_id": 1})
        self.assertEqual(r.status_code, 201)
        e = r.get_json()
        nueva = max(e["actividades"], key=lambda a: a["id"])
        r = self.c.patch(f"/api/v1/actividades/{nueva['id']}/completada", json={"completada": True})
        self.assertTrue(next(a for a in r.get_json()["actividades"] if a["id"] == nueva["id"])["completada"])

    def test_rn01_incompleta(self):
        r = self.c.post("/api/v1/actividades", json={"nombre": "", "fecha_limite": "2026-12-01",
                                                      "horas_estimadas": 3, "materia_id": 1})
        self.assertEqual(r.status_code, 400)
        r = self.c.post("/api/v1/actividades", json={"nombre": "x" * 5, "materia_id": 1})
        self.assertEqual(r.status_code, 400)

    def test_rn02_horas(self):
        base = {d: 1 for d in ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")}
        self.assertEqual(self.c.put("/api/v1/disponibilidad", json={**base, "Lunes": 25}).status_code, 400)
        self.assertEqual(self.c.put("/api/v1/disponibilidad", json={**base, "Lunes": 0}).status_code, 200)

    def test_cero_horas_disponibles(self):
        z = {d: 0 for d in ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")}
        e = self.c.put("/api/v1/disponibilidad", json=z).get_json()
        self.assertIsNone(e["resumen"]["carga"]["nivel"])
        self.assertIn("Registra tus horas", e["resumen"]["carga"]["mensaje"])

    def test_bug002_sin_pendientes(self):
        for a in self.estado()["actividades"]:
            self.c.patch(f"/api/v1/actividades/{a['id']}/completada", json={"completada": True})
        self.assertEqual(self.estado()["resumen"]["carga"]["mensaje"],
                         "Aún no tienes actividades pendientes")

    def test_materia_con_actividades_no_se_borra(self):
        self.assertEqual(self.c.delete("/api/v1/materias/1").status_code, 400)

    def test_sesiones_aisladas(self):
        otro = crear_app(GestorDeSesiones()).test_client()
        self.c.delete("/api/v1/actividades/1")
        self.assertEqual(len(otro.get("/api/v1/estado").get_json()["actividades"]), 5)
        self.assertEqual(len(self.estado()["actividades"]), 4)

    def test_reiniciar(self):
        self.c.delete("/api/v1/actividades/1")
        self.assertEqual(len(self.c.post("/api/v1/reiniciar").get_json()["actividades"]), 5)

    def test_salud_informa_version_sin_datos(self):
        r = self.c.get("/salud").get_json()
        self.assertEqual(r["estado"], "ok")
        self.assertRegex(r["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(set(r), {"estado", "version", "persistencia", "esquema"})

    def test_cookie_httponly(self):
        r = self.c.get("/api/v1/estado")
        self.assertIn("HttpOnly", r.headers["Set-Cookie"])
        self.assertIn("SameSite=Lax", r.headers["Set-Cookie"])


if __name__ == "__main__":
    unittest.main()
