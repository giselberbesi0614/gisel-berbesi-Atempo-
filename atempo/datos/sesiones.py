"""Sesiones de demostración en memoria (RN-06: solo datos ficticios)."""
from __future__ import annotations

import secrets
import threading
import time
from datetime import date, timedelta

from ..dominio.errores import ErrorDeDominio, ErrorNoEncontrado
from ..dominio.modelos import DIAS, Actividad, Materia, validar_horas

COLORES = ("#6C5CE7", "#00A6A6", "#F08A5D", "#E85D75", "#3B82F6", "#8B5CF6")


def datos_demo(hoy: date):
    materias = [
        Materia(1, "Diseño de Interfaces", "Docente demo A", COLORES[0]),
        Materia(2, "Programación Web", "Docente demo B", COLORES[1]),
        Materia(3, "Matemáticas", "Docente demo C", COLORES[2]),
        Materia(4, "Investigación", "Docente demo D", COLORES[3]),
    ]
    d = lambda n: hoy + timedelta(days=n)  # noqa: E731
    actividades = [
        Actividad(1, "Prototipo de aplicación", d(1), 4, False, 1),
        Actividad(2, "Ejercicios de derivadas", d(2), 2, False, 3),
        Actividad(3, "Entrega API REST", d(4), 5, False, 2),
        Actividad(4, "Lectura y mapa conceptual", d(6), 3, False, 4),
        Actividad(5, "Wireframes iniciales", d(-2), 2, True, 1),
    ]
    disp = dict(zip(DIAS, (4, 3, 4, 2, 3, 2, 1)))
    return materias, actividades, disp


class SesionDemo:
    """Implementa FuenteDeDatos y las operaciones de escritura; protegida por un lock."""

    def __init__(self, hoy: date | None = None):
        self.lock = threading.RLock()
        self.hoy = hoy or date.today()
        self.reiniciar()
        self.ultimo_uso = time.time()

    def reiniciar(self):
        with self.lock:
            m, a, d = datos_demo(self.hoy)
            self._m = {x.id: x for x in m}
            self._a = {x.id: x for x in a}
            self._d = d
            self._sig = 100

    def _id(self):
        self._sig += 1
        return self._sig

    # --- lectura (FuenteDeDatos)
    def materias(self):
        with self.lock:
            return list(self._m.values())

    def actividades(self):
        with self.lock:
            return list(self._a.values())

    def disponibilidad(self):
        with self.lock:
            return dict(self._d)

    def horas_disponibles(self):
        with self.lock:
            return float(sum(self._d.values()))

    # --- escritura
    def guardar_materia(self, datos: dict, id: int | None = None) -> Materia:
        with self.lock:
            mid = id or self._id()
            if id and id not in self._m:
                raise ErrorNoEncontrado("materia")
            m = Materia(mid, str(datos.get("nombre", "")).strip(),
                        str(datos.get("docente", "")).strip(),
                        datos.get("color") or COLORES[0])
            self._m[mid] = m
            return m

    def eliminar_materia(self, id: int):
        with self.lock:
            if id not in self._m:
                raise ErrorNoEncontrado("materia")
            if any(a.materia_id == id for a in self._a.values()):
                raise ErrorDeDominio("Elimina primero las actividades de esta materia.")
            del self._m[id]

    def guardar_actividad(self, datos: dict, id: int | None = None) -> Actividad:
        with self.lock:
            if id and id not in self._a:
                raise ErrorNoEncontrado("actividad")
            try:
                fecha = date.fromisoformat(str(datos.get("fecha_limite", "")))
            except ValueError:
                fecha = None
            materia_id = datos.get("materia_id")
            if materia_id is not None and materia_id not in self._m:
                raise ErrorDeDominio("Selecciona una materia válida.")
            previa = self._a.get(id) if id else None
            a = Actividad(id or self._id(), str(datos.get("nombre", "")),
                          fecha, datos.get("horas_estimadas"),
                          previa.completada if previa else False, materia_id)
            self._a[a.id] = a
            return a

    def cambiar_estado(self, id: int, completada: bool) -> Actividad:
        with self.lock:
            a = self._a.get(id)
            if not a:
                raise ErrorNoEncontrado("actividad")
            a = a.marcar_completada() if completada else a.reabrir()
            self._a[id] = a
            return a

    def eliminar_actividad(self, id: int):
        with self.lock:
            if id not in self._a:
                raise ErrorNoEncontrado("actividad")
            del self._a[id]

    def guardar_disponibilidad(self, datos: dict):
        with self.lock:
            nueva = {}
            for dia in DIAS:           # RN-02: una entrada por día, 0–24 h
                nueva[dia] = validar_horas(datos.get(dia, 0))
            self._d = nueva


class GestorDeSesiones:
    """Una SesionDemo por visitante, con TTL y tope (un proceso, varios hilos)."""

    def __init__(self, maximo: int = 200, ttl: int = 3600):
        self.maximo, self.ttl = maximo, ttl
        self._s: dict[str, SesionDemo] = {}
        self._lock = threading.Lock()

    def _purgar(self, ahora):
        for k in [k for k, v in self._s.items() if ahora - v.ultimo_uso > self.ttl]:
            del self._s[k]

    def obtener(self, sid: str | None) -> tuple[str, SesionDemo]:
        ahora = time.time()
        with self._lock:
            self._purgar(ahora)
            if sid in self._s:
                s = self._s[sid]
                s.ultimo_uso = ahora
                return sid, s
            if len(self._s) >= self.maximo:
                viejo = min(self._s, key=lambda k: self._s[k].ultimo_uso)
                del self._s[viejo]
            sid = secrets.token_urlsafe(24)
            self._s[sid] = SesionDemo()
            return sid, self._s[sid]
