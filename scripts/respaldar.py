"""Respaldo seguro de la base SQLite de Atempo (funciona aunque la aplicación esté en uso).
Uso: python scripts/respaldar.py /data/atempo.db /data/respaldo.db"""
import os
import sqlite3
import sys

if len(sys.argv) != 3:
    sys.exit("Uso: python scripts/respaldar.py ORIGEN.db DESTINO.db")
origen, destino = sys.argv[1], sys.argv[2]
if not os.path.isfile(origen):                      # sqlite3.connect crearía una base vacía en silencio
    sys.exit(f"No existe la base de origen: {origen}")
if os.path.abspath(origen) == os.path.abspath(destino):
    sys.exit("El destino no puede ser el mismo archivo que el origen.")
a, b = sqlite3.connect(origen), sqlite3.connect(destino)
a.backup(b)
estado = b.execute("PRAGMA integrity_check").fetchone()[0]
a.close()
b.close()
print(f"Respaldo en {destino}: integrity_check = {estado}")
sys.exit(0 if estado == "ok" else 1)
