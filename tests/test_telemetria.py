"""Observabilidad: log JSON sin PII, trace_id, métricas por plantilla de ruta, muestreo y /metrics opcional."""
import json
import os
import unittest
from unittest import mock

from atempo.datos.sesiones import GestorDeSesiones
from atempo.web import crear_app


def cliente(**env):
    with mock.patch.dict(os.environ, {k: str(v) for k, v in env.items()}):
        app = crear_app(GestorDeSesiones())
    return app, app.test_client()


class TestTelemetria(unittest.TestCase):
    def lineas(self, cm):
        return [json.loads(x.split(":", 2)[2]) for x in cm.output]

    def test_log_json_con_campos_y_trace_id(self):
        _, c = cliente(ATEMPO_LOG_MUESTREO=1)
        with self.assertLogs("atempo.telemetria", "INFO") as cm:
            r = c.get("/api/v1/estado", headers={"X-Request-ID": "abc12345-trace"})
        d = self.lineas(cm)[0]
        self.assertEqual(r.headers["X-Request-ID"], "abc12345-trace")
        self.assertEqual((d["trace_id"], d["metodo"], d["ruta"], d["estado"]),
                         ("abc12345-trace", "GET", "/api/v1/estado", 200))
        self.assertIn("duracion_ms", d)

    def test_trace_id_invalido_se_reemplaza(self):
        _, c = cliente(ATEMPO_LOG_MUESTREO=1)
        r = c.get("/api/v1/estado", headers={"X-Request-ID": "<script>x</script>"})
        self.assertRegex(r.headers["X-Request-ID"], r"^[0-9a-f]{32}$")

    def test_el_log_no_contiene_pii_ni_ids(self):
        _, c = cliente(ATEMPO_LOG_MUESTREO=1)
        with self.assertLogs("atempo.telemetria", "INFO") as cm:
            c.post("/api/v1/materias", json={"nombre": "Juan Pérez 1098765432", "docente": "Ana Gómez"})
            c.put("/api/v1/materias/4321", json={"nombre": "Otra"})
        texto = "\n".join(cm.output)
        for prohibido in ("Juan", "1098765432", "Ana", "4321", "atempo_sid"):
            self.assertNotIn(prohibido, texto)
        self.assertIn("/api/v1/materias/<int:id>", texto)

    def test_errores_se_registran_aunque_el_muestreo_sea_cero(self):
        _, c = cliente(ATEMPO_LOG_MUESTREO=0)
        with self.assertLogs("atempo.telemetria", "INFO") as cm:
            c.get("/api/v1/estado")                                   # 200: no se registra
            c.delete("/api/v1/materias/999")                          # 404: se registra
        self.assertEqual([d["estado"] for d in self.lineas(cm)], [404])

    def test_metrics_apagado_por_defecto(self):
        _, c = cliente()
        self.assertEqual(c.get("/metrics").status_code, 404)

    def test_metrics_cuenta_y_acumula_el_histograma(self):
        _, c = cliente(ATEMPO_METRICAS=1, ATEMPO_LOG_MUESTREO=0)
        for _ in range(3):
            c.get("/api/v1/estado")
        c.delete("/api/v1/materias/999")
        t = c.get("/metrics").get_data(as_text=True)
        self.assertIn('atempo_http_requests_total{method="GET",route="/api/v1/estado",status="200"} 3', t)
        self.assertIn('atempo_http_requests_total{method="DELETE",route="/api/v1/materias/<int:id>",status="404"} 1', t)
        self.assertIn('atempo_http_request_duration_ms_count{route="/api/v1/estado"} 3', t)
        self.assertIn('atempo_http_request_duration_ms_bucket{route="/api/v1/estado",le="+Inf"} 3', t)
        self.assertNotIn('route="/metrics"', t)


if __name__ == "__main__":
    unittest.main()
