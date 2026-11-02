"""Seguridad (DevSecOps): cookie Secure tras un proxy, HSTS, CSP anti-clickjacking, solo JSON y SQL con lista blanca."""
import os
import unittest
from unittest import mock

from atempo.datos.sesiones import GestorDeSesiones
from atempo.datos.sqlite import Repositorio
from atempo.web import crear_app

HTTPS = {"X-Forwarded-Proto": "https"}


class TestSeguridad(unittest.TestCase):
    def cliente(self, proxy):
        env = {"ATEMPO_PROXY": "1"} if proxy else {}
        with mock.patch.dict(os.environ, env, clear=False):
            if not proxy:
                os.environ.pop("ATEMPO_PROXY", None)
            return crear_app(GestorDeSesiones()).test_client()

    def test_cookie_secure_y_hsts_detras_de_proxy_https(self):
        r = self.cliente(True).get("/api/v1/estado", headers=HTTPS)
        self.assertIn("Secure", r.headers["Set-Cookie"])
        self.assertIn("max-age=", r.headers["Strict-Transport-Security"])

    def test_sin_proxy_confiable_se_ignora_la_cabecera(self):
        r = self.cliente(False).get("/api/v1/estado", headers=HTTPS)
        self.assertNotIn("Secure", r.headers["Set-Cookie"])
        self.assertNotIn("Strict-Transport-Security", r.headers)

    def test_csp_impide_ser_incrustada(self):
        r = self.cliente(False).get("/")
        self.assertIn("frame-ancestors 'none'", r.headers["Content-Security-Policy"])

    def test_la_api_solo_acepta_json(self):
        c = self.cliente(False)
        for tipo in ("text/plain", "application/x-www-form-urlencoded"):
            r = c.post("/api/v1/materias", data='{"nombre":"x"}', headers={"Content-Type": tipo})
            self.assertEqual(r.status_code, 400, tipo)

    def test_consulta_con_tabla_desconocida_se_rechaza(self):
        repo = Repositorio(":memory:")
        self.addCleanup(repo.cerrar)
        _, sesion = repo.obtener(None)
        with self.assertRaises(ValueError):
            sesion._existe("materia; DROP TABLE materia", 1)


if __name__ == "__main__":
    unittest.main()
