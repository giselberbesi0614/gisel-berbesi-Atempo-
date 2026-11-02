"""Telemetría de Atempo sin dependencias: log JSON, métricas estilo Prometheus e identificador de traza por petición.

- Traza: cada petición recibe un trace_id (X-Request-ID si es válido, si no uno nuevo) que vuelve en la respuesta.
- Métricas: contadores y un histograma de latencia por ruta (plantilla, nunca la URL real), en /metrics (opcional).
- Logs: una línea JSON por petición. Nunca incluye cuerpo, cookies, nombres ni ids de recursos (sin PII).
- Muestreo: solo las respuestas < 400 se muestrean (ATEMPO_LOG_MUESTREO, 0 a 1); los errores se registran siempre.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import uuid
import zlib

from flask import Flask, Response, g, request

CUBOS_MS = (5, 10, 25, 50, 100, 250, 500, 1000)
_ID_VALIDO = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
log = logging.getLogger("atempo.telemetria")


class Metricas:
    def __init__(self):
        self.lock = threading.Lock()
        self.peticiones: dict[tuple, int] = {}
        self.latencia: dict[str, list] = {}      # ruta -> [conteo por cubo..., total, suma_ms]

    def observar(self, metodo: str, ruta: str, estado: int, ms: float):
        with self.lock:
            k = (metodo, ruta, str(estado))
            self.peticiones[k] = self.peticiones.get(k, 0) + 1
            h = self.latencia.setdefault(ruta, [0] * len(CUBOS_MS) + [0, 0.0])
            for i, limite in enumerate(CUBOS_MS):
                if ms <= limite:
                    h[i] += 1
            h[-2] += 1
            h[-1] += ms

    def texto(self) -> str:
        out = ["# TYPE atempo_http_requests_total counter"]
        with self.lock:
            for (m, r, e), n in sorted(self.peticiones.items()):
                out.append(f'atempo_http_requests_total{{method="{m}",route="{r}",status="{e}"}} {n}')
            out.append("# TYPE atempo_http_request_duration_ms histogram")
            for r, h in sorted(self.latencia.items()):
                for limite, n in zip(CUBOS_MS, h):
                    out.append(f'atempo_http_request_duration_ms_bucket{{route="{r}",le="{limite}"}} {n}')
                out.append(f'atempo_http_request_duration_ms_bucket{{route="{r}",le="+Inf"}} {h[-2]}')
                out.append(f'atempo_http_request_duration_ms_sum{{route="{r}"}} {h[-1]:.3f}')
                out.append(f'atempo_http_request_duration_ms_count{{route="{r}"}} {h[-2]}')
        return "\n".join(out) + "\n"


def _muestrear(trace_id: str, tasa: float) -> bool:
    """Decisión determinista por traza: misma traza, misma decisión."""
    return tasa >= 1 or (tasa > 0 and (zlib.crc32(trace_id.encode()) % 10000) / 10000 < tasa)


def instalar(app: Flask) -> Metricas:
    metricas = Metricas()
    app.config["METRICAS"] = metricas
    tasa = float(os.environ.get("ATEMPO_LOG_MUESTREO", "0.2"))
    expone = os.environ.get("ATEMPO_METRICAS") == "1"

    @app.before_request
    def _inicio():
        pedido = request.headers.get("X-Request-ID", "")
        g.trace_id = pedido if _ID_VALIDO.match(pedido) else uuid.uuid4().hex
        g.t0 = time.perf_counter()

    @app.after_request
    def _fin(r: Response):
        if not hasattr(g, "t0"):
            return r
        ms = (time.perf_counter() - g.t0) * 1000
        ruta = request.url_rule.rule if request.url_rule else "(sin ruta)"
        r.headers["X-Request-ID"] = g.trace_id
        if ruta != "/metrics":
            metricas.observar(request.method, ruta, r.status_code, ms)
            if r.status_code >= 400 or _muestrear(g.trace_id, tasa):
                nivel = "ERROR" if r.status_code >= 500 else "WARN" if r.status_code >= 400 else "INFO"
                log.info(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "nivel": nivel,
                                     "trace_id": g.trace_id, "metodo": request.method, "ruta": ruta,
                                     "estado": r.status_code, "duracion_ms": round(ms, 2)}, ensure_ascii=False))
        return r

    if expone:
        @app.get("/metrics")
        def _metrics():
            return Response(metricas.texto(), mimetype="text/plain; version=0.0.4")
    return metricas
