"""Adaptador SQLite: misma batería que la memoria, persistencia tras reiniciar y esquema versionado."""
import os
import sqlite3
import tempfile
import threading
import unittest

from atempo.datos.sqlite import VERSION_ESQUEMA, Repositorio
from atempo.dominio.errores import ErrorDeDominio
from atempo.web import crear_app
from tests import test_api
from tests.test_robustez import ACT

DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


class _Cierra:
    def nuevo(self, *a, **k):
        r = Repositorio(*a, **k)
        self.addCleanup(r.cerrar)
        return r


class TestApiSobreSQLite(_Cierra, test_api.TestApi):
    """Reutiliza las 10 pruebas de la API con la fuente de datos SQLite (sustitución de Liskov/DIP)."""

    def setUp(self):
        self.c = crear_app(self.nuevo(":memory:")).test_client()

    def test_sesiones_aisladas(self):                      # dos clientes sobre la MISMA base
        repo = self.nuevo(":memory:")
        a, b = crear_app(repo).test_client(), crear_app(repo).test_client()
        a.get("/api/v1/estado"); b.get("/api/v1/estado")
        a.delete("/api/v1/actividades/1")
        self.assertEqual(len(a.get("/api/v1/estado").get_json()["actividades"]), 4)
        self.assertEqual(len(b.get("/api/v1/estado").get_json()["actividades"]), 5)


class TestPersistencia(_Cierra, unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.dir.name, "atempo.db")

    def tearDown(self):
        self.dir.cleanup()

    def test_los_datos_sobreviven_al_reinicio(self):
        r1 = self.nuevo(self.ruta)
        sid, s = r1.obtener(None)
        s.guardar_actividad({**ACT, "nombre": "Sobrevive"})
        r1.cerrar()
        r2 = self.nuevo(self.ruta)                                      # "reinicio del servidor"
        sid2, s2 = r2.obtener(sid)
        self.assertEqual(sid2, sid)
        self.assertIn("Sobrevive", [a.nombre for a in s2.actividades()])

    def test_sesion_desconocida_crea_otra(self):
        r = self.nuevo(":memory:")
        sid, _ = r.obtener("no-existe")
        self.assertNotEqual(sid, "no-existe")

    def test_esquema_versionado_e_idempotente(self):
        self.nuevo(self.ruta).cerrar()
        r = self.nuevo(self.ruta)                                       # reabrir no repite la migración
        self.assertEqual(r.version(), VERSION_ESQUEMA)

    def test_esquema_mas_nuevo_se_rechaza(self):
        self.nuevo(self.ruta).cerrar()
        con = sqlite3.connect(self.ruta); con.execute("PRAGMA user_version = 99"); con.close()
        with self.assertRaises(RuntimeError):
            self.nuevo(self.ruta)

    def test_rechazo_hace_rollback(self):
        r = self.nuevo(":memory:"); _, s = r.obtener(None)
        antes = s.actividades()
        with self.assertRaises(ErrorDeDominio):
            s.guardar_actividad({**ACT, "nombre": ""})
        with self.assertRaises(ErrorDeDominio):
            s.guardar_disponibilidad({**{d: 1 for d in DIAS}, "Lunes": 30})
        self.assertEqual(antes, s.actividades())

    def test_restricciones_de_la_base(self):
        r = self.nuevo(":memory:"); sid, s = r.obtener(None)
        with self.assertRaises(sqlite3.IntegrityError):                  # la base también defiende RN-02
            r.con.execute("INSERT INTO disponibilidad VALUES (?, 'Lunes', 25)", (sid,))

    def test_concurrencia_sin_perdidas(self):
        r = self.nuevo(self.ruta); _, s = r.obtener(None)
        def trabajo():
            for _ in range(20):
                s.guardar_actividad(ACT)
        hilos = [threading.Thread(target=trabajo) for _ in range(6)]
        [h.start() for h in hilos]; [h.join() for h in hilos]
        ids = [a.id for a in s.actividades()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 5 + 6 * 20)

    def test_purga_por_ttl(self):
        r = self.nuevo(":memory:", ttl=-1)                              # todo vencido
        sid, _ = r.obtener(None)
        r.purgar()
        self.assertIsNone(r.con.execute("SELECT 1 FROM sesion WHERE id=?", (sid,)).fetchone())
        self.assertIsNone(r.con.execute("SELECT 1 FROM actividad WHERE sesion_id=?", (sid,)).fetchone())


if __name__ == "__main__":
    unittest.main()
