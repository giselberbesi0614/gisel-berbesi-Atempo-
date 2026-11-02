"""Fábrica de la aplicación Flask y API REST /api/v1."""
from __future__ import annotations

import os

from flask import Blueprint, Flask, current_app, g, jsonify, make_response, render_template, request

from ..datos.sesiones import GestorDeSesiones
from ..datos.sqlite import Repositorio
from ..dominio.errores import ErrorDeDominio, ErrorNoEncontrado
from ..servicios.dashboard import Dashboard

api = Blueprint("api", __name__, url_prefix="/api/v1")
COOKIE = "atempo_sid"


def _ser(a):
    return {"id": a.id, "nombre": a.nombre, "fecha_limite": a.fecha_limite.isoformat(),
            "horas_estimadas": a.horas_estimadas, "completada": a.completada,
            "materia_id": a.materia_id}


def _estado(s):
    return {
        "materias": [{"id": m.id, "nombre": m.nombre, "docente": m.docente, "color": m.color}
                     for m in s.materias()],
        "actividades": [_ser(a) for a in s.actividades()],
        "disponibilidad": s.disponibilidad(),
        "resumen": Dashboard(s).resumen(),
    }


def _sesion():
    if "sesion" not in g:     # una sola sesión por petición
        g.sesion = current_app.config["GESTOR"].obtener(request.cookies.get(COOKIE))
    return g.sesion


def _resp(payload, status=200):
    sid, _ = _sesion()
    r = make_response(jsonify(payload), status)
    r.set_cookie(COOKIE, sid, httponly=True, samesite="Lax",
                 secure=request.is_secure, max_age=3600)
    return r


def _json():
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        raise ErrorDeDominio("Cuerpo JSON inválido.")
    return d


@api.errorhandler(ErrorDeDominio)
def _error(e):
    return jsonify({"error": str(e)}), 400


@api.errorhandler(ErrorNoEncontrado)
def _no_encontrado(e):
    return jsonify({"error": str(e)}), 404


@api.get("/estado")
def estado():
    return _resp(_estado(_sesion()[1]))


@api.post("/materias")
def crear_materia():
    s = _sesion()[1]
    s.guardar_materia(_json())
    return _resp(_estado(s), 201)


@api.put("/materias/<int:id>")
def editar_materia(id):
    s = _sesion()[1]
    s.guardar_materia(_json(), id)
    return _resp(_estado(s))


@api.delete("/materias/<int:id>")
def borrar_materia(id):
    s = _sesion()[1]
    s.eliminar_materia(id)
    return _resp(_estado(s))


@api.post("/actividades")
def crear_actividad():
    s = _sesion()[1]
    s.guardar_actividad(_json())
    return _resp(_estado(s), 201)


@api.put("/actividades/<int:id>")
def editar_actividad(id):
    s = _sesion()[1]
    s.guardar_actividad(_json(), id)
    return _resp(_estado(s))


@api.patch("/actividades/<int:id>/completada")
def estado_actividad(id):
    s = _sesion()[1]
    s.cambiar_estado(id, bool(_json().get("completada")))
    return _resp(_estado(s))


@api.delete("/actividades/<int:id>")
def borrar_actividad(id):
    s = _sesion()[1]
    s.eliminar_actividad(id)
    return _resp(_estado(s))


@api.put("/disponibilidad")
def disponibilidad():
    s = _sesion()[1]
    s.guardar_disponibilidad(_json())
    return _resp(_estado(s))


@api.post("/reiniciar")
def reiniciar():
    s = _sesion()[1]
    s.reiniciar()
    return _resp(_estado(s))


def crear_app(gestor=None) -> Flask:
    """Con ATEMPO_DB=ruta.db los datos de cada sesión se guardan en SQLite; sin ella viven en memoria."""
    app = Flask(__name__)
    if gestor is None:
        ruta = os.environ.get("ATEMPO_DB")
        gestor = Repositorio(ruta) if ruta else GestorDeSesiones()
    app.config["GESTOR"] = gestor
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    if os.environ.get("ATEMPO_PROXY") == "1":     # detrás de un proxy TLS (Render, etc.): confiar en X-Forwarded-Proto
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    from .telemetria import instalar
    instalar(app)
    app.register_blueprint(api)

    @app.get("/")
    def inicio():
        return render_template("index.html")

    @app.get("/salud")
    def salud():
        """Comprobación de salud: versión, tipo de persistencia y esquema. No expone rutas ni datos."""
        from .. import __version__
        g = app.config["GESTOR"]
        persistente = isinstance(g, Repositorio)
        return {"estado": "ok", "version": __version__,
                "persistencia": "sqlite" if persistente else "memoria",
                "esquema": g.version() if persistente else None}

    @app.after_request
    def cabeceras(r):
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
            "style-src-attr 'unsafe-inline'; "
            "font-src https://fonts.gstatic.com; img-src 'self' data:; frame-ancestors 'none'")
        if request.is_secure:
            r.headers["Strict-Transport-Security"] = "max-age=31536000"
        return r

    return app
