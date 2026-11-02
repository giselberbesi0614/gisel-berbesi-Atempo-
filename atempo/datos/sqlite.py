"""Adaptador SQLite: mismo contrato que SesionDemo (FuenteDeDatos), con transacciones y esquema versionado."""
from __future__ import annotations

import secrets
import sqlite3
import threading
import time
from datetime import date

from ..dominio.errores import ErrorDeDominio, ErrorNoEncontrado
from ..dominio.modelos import DIAS, Actividad, Materia, validar_horas
from .sesiones import COLORES, datos_demo

VERSION_ESQUEMA = 1
MIGRACIONES = {
    1: """
    CREATE TABLE sesion (id TEXT PRIMARY KEY, ultimo_uso REAL NOT NULL);
    CREATE TABLE materia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sesion_id TEXT NOT NULL REFERENCES sesion(id) ON DELETE CASCADE,
        nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
        docente TEXT NOT NULL DEFAULT '', color TEXT NOT NULL);
    CREATE TABLE actividad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sesion_id TEXT NOT NULL REFERENCES sesion(id) ON DELETE CASCADE,
        materia_id INTEGER NOT NULL REFERENCES materia(id),
        nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
        fecha_limite TEXT NOT NULL,
        horas_estimadas REAL NOT NULL CHECK (horas_estimadas > 0),
        completada INTEGER NOT NULL DEFAULT 0 CHECK (completada IN (0, 1)));
    CREATE TABLE disponibilidad (
        sesion_id TEXT NOT NULL REFERENCES sesion(id) ON DELETE CASCADE,
        dia TEXT NOT NULL, horas REAL NOT NULL CHECK (horas >= 0 AND horas <= 24),
        PRIMARY KEY (sesion_id, dia));
    """,
}


class Repositorio:
    """Una conexión por proceso, protegida por un lock; cada operación de escritura es una transacción."""

    def __init__(self, ruta: str = ":memory:", ttl: int = 3600):
        self.ttl = ttl
        self.lock = threading.RLock()
        self.con = sqlite3.connect(ruta, check_same_thread=False, isolation_level=None)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        try:
            self._migrar()
        except Exception:
            self.con.close()          # no dejar la conexión abierta si el arranque se rechaza
            raise

    def _migrar(self):
        with self.lock:
            actual = self.con.execute("PRAGMA user_version").fetchone()[0]
            if actual > VERSION_ESQUEMA:
                raise RuntimeError(f"La base tiene el esquema v{actual}, más nuevo que esta versión "
                                   f"(v{VERSION_ESQUEMA}).")
            for v in range(actual + 1, VERSION_ESQUEMA + 1):
                self.con.execute("BEGIN")
                try:
                    for sentencia in MIGRACIONES[v].split(";"):
                        if sentencia.strip():
                            self.con.execute(sentencia)
                    self.con.execute(f"PRAGMA user_version = {v}")
                    self.con.execute("COMMIT")
                except Exception:
                    self.con.execute("ROLLBACK")
                    raise

    def version(self) -> int:
        with self.lock:
            return self.con.execute("PRAGMA user_version").fetchone()[0]

    def purgar(self):
        with self.lock:
            self.con.execute("DELETE FROM sesion WHERE ultimo_uso < ?", (time.time() - self.ttl,))

    def obtener(self, sid: str | None) -> tuple[str, "SesionSQLite"]:
        with self.lock:
            self.purgar()
            if sid and self.con.execute("SELECT 1 FROM sesion WHERE id=?", (sid,)).fetchone():
                self.con.execute("UPDATE sesion SET ultimo_uso=? WHERE id=?", (time.time(), sid))
                return sid, SesionSQLite(self, sid)
            sid = secrets.token_urlsafe(24)
            s = SesionSQLite(self, sid, nueva=True)
            return sid, s

    def cerrar(self):
        self.con.close()


class SesionSQLite:
    def __init__(self, repo: Repositorio, sid: str, nueva: bool = False, hoy: date | None = None):
        self.repo, self.sid, self.hoy = repo, sid, hoy or date.today()
        self.lock = repo.lock
        if nueva:
            self.reiniciar()

    @property
    def _c(self):
        return self.repo.con

    def _tx(self):
        return _Transaccion(self._c, self.lock)

    # --- lectura (FuenteDeDatos)
    def materias(self):
        with self.lock:
            f = self._c.execute("SELECT * FROM materia WHERE sesion_id=? ORDER BY id", (self.sid,)).fetchall()
        return [Materia(r["id"], r["nombre"], r["docente"], r["color"]) for r in f]

    def actividades(self):
        with self.lock:
            f = self._c.execute("SELECT * FROM actividad WHERE sesion_id=? ORDER BY id", (self.sid,)).fetchall()
        return [self._act(r) for r in f]

    @staticmethod
    def _act(r):
        return Actividad(r["id"], r["nombre"], date.fromisoformat(r["fecha_limite"]),
                         r["horas_estimadas"], bool(r["completada"]), r["materia_id"])

    def disponibilidad(self):
        with self.lock:
            f = self._c.execute("SELECT dia, horas FROM disponibilidad WHERE sesion_id=?", (self.sid,)).fetchall()
        d = {r["dia"]: r["horas"] for r in f}
        return {dia: d.get(dia, 0.0) for dia in DIAS}

    def horas_disponibles(self):
        return float(sum(self.disponibilidad().values()))

    # --- escritura (cada método es una transacción)
    def reiniciar(self):
        m, a, disp = datos_demo(self.hoy)
        with self._tx() as c:
            c.execute("INSERT OR REPLACE INTO sesion (id, ultimo_uso) VALUES (?, ?)", (self.sid, time.time()))
            for t in ("actividad", "materia", "disponibilidad"):
                c.execute(f"DELETE FROM {t} WHERE sesion_id=?", (self.sid,))
            mapa = {}
            for x in m:
                cur = c.execute("INSERT INTO materia (sesion_id, nombre, docente, color) VALUES (?,?,?,?)",
                                (self.sid, x.nombre, x.docente, x.color))
                mapa[x.id] = cur.lastrowid
            for x in a:
                c.execute("INSERT INTO actividad (sesion_id, materia_id, nombre, fecha_limite, "
                          "horas_estimadas, completada)"
                          " VALUES (?,?,?,?,?,?)", (self.sid, mapa[x.materia_id], x.nombre,
                                                    x.fecha_limite.isoformat(), x.horas_estimadas, int(x.completada)))
            for dia, h in disp.items():
                c.execute("INSERT INTO disponibilidad (sesion_id, dia, horas) VALUES (?,?,?)", (self.sid, dia, h))

    def _existe(self, tabla, id):
        if tabla not in ("materia", "actividad"):      # lista blanca: el nombre se inserta en el SQL
            raise ValueError(f"Tabla no permitida: {tabla}")
        return self._c.execute(f"SELECT 1 FROM {tabla} WHERE id=? AND sesion_id=?", (id, self.sid)).fetchone()

    def guardar_materia(self, datos: dict, id: int | None = None) -> Materia:
        with self._tx() as c:
            if id and not self._existe("materia", id):
                raise ErrorNoEncontrado("materia")
            m = Materia(id or 0, str(datos.get("nombre", "")).strip(), str(datos.get("docente", "")).strip(),
                        datos.get("color") or COLORES[0])          # valida RN en el dominio
            if id:
                c.execute("UPDATE materia SET nombre=?, docente=?, color=? WHERE id=?",
                          (m.nombre, m.docente, m.color, id))
                return Materia(id, m.nombre, m.docente, m.color)
            cur = c.execute("INSERT INTO materia (sesion_id, nombre, docente, color) VALUES (?,?,?,?)",
                            (self.sid, m.nombre, m.docente, m.color))
            return Materia(cur.lastrowid, m.nombre, m.docente, m.color)

    def eliminar_materia(self, id: int):
        with self._tx() as c:
            if not self._existe("materia", id):
                raise ErrorNoEncontrado("materia")
            if c.execute("SELECT 1 FROM actividad WHERE materia_id=?", (id,)).fetchone():
                raise ErrorDeDominio("Elimina primero las actividades de esta materia.")
            c.execute("DELETE FROM materia WHERE id=?", (id,))

    def guardar_actividad(self, datos: dict, id: int | None = None) -> Actividad:
        with self._tx() as c:
            if id and not self._existe("actividad", id):
                raise ErrorNoEncontrado("actividad")
            try:
                fecha = date.fromisoformat(str(datos.get("fecha_limite", "")))
            except ValueError:
                fecha = None
            mid = datos.get("materia_id")
            if mid is not None and not self._existe("materia", mid):
                raise ErrorDeDominio("Selecciona una materia válida.")
            previa = c.execute("SELECT completada FROM actividad WHERE id=?", (id,)).fetchone() if id else None
            a = Actividad(id or 0, str(datos.get("nombre", "")), fecha, datos.get("horas_estimadas"),
                          bool(previa["completada"]) if previa else False, mid)     # valida RN-01 en el dominio
            if id:
                c.execute("UPDATE actividad SET materia_id=?, nombre=?, fecha_limite=?, horas_estimadas=? WHERE id=?",
                          (a.materia_id, a.nombre.strip(), a.fecha_limite.isoformat(), a.horas_estimadas, id))
                return Actividad(id, a.nombre, a.fecha_limite, a.horas_estimadas, a.completada, a.materia_id)
            cur = c.execute("INSERT INTO actividad (sesion_id, materia_id, nombre, fecha_limite, horas_estimadas)"
                            " VALUES (?,?,?,?,?)", (self.sid, a.materia_id, a.nombre.strip(),
                                                    a.fecha_limite.isoformat(), a.horas_estimadas))
            return Actividad(cur.lastrowid, a.nombre, a.fecha_limite, a.horas_estimadas, False, a.materia_id)

    def cambiar_estado(self, id: int, completada: bool) -> Actividad:
        with self._tx() as c:
            if not self._existe("actividad", id):
                raise ErrorNoEncontrado("actividad")
            c.execute("UPDATE actividad SET completada=? WHERE id=?", (int(bool(completada)), id))
            return self._act(c.execute("SELECT * FROM actividad WHERE id=?", (id,)).fetchone())

    def eliminar_actividad(self, id: int):
        with self._tx() as c:
            if not self._existe("actividad", id):
                raise ErrorNoEncontrado("actividad")
            c.execute("DELETE FROM actividad WHERE id=?", (id,))

    def guardar_disponibilidad(self, datos: dict):
        # valida los 7 días antes de escribir (RN-02)
        nueva = {dia: validar_horas(datos.get(dia, 0)) for dia in DIAS}
        with self._tx() as c:
            for dia, h in nueva.items():
                c.execute("INSERT OR REPLACE INTO disponibilidad (sesion_id, dia, horas) VALUES (?,?,?)",
                          (self.sid, dia, h))


class _Transaccion:
    def __init__(self, con, lock):
        self.con, self.lock = con, lock

    def __enter__(self):
        self.lock.acquire()
        self.con.execute("BEGIN IMMEDIATE")
        return self.con

    def __exit__(self, tipo, valor, tb):
        try:
            self.con.execute("ROLLBACK" if tipo else "COMMIT")
        finally:
            self.lock.release()
        return False
