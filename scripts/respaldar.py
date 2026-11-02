"""Respaldo seguro de la base SQLite de Atempo (funciona aunque la aplicación esté en uso).
Uso: python scripts/respaldar.py /data/atempo.db /data/respaldo.db"""
import sqlite3
import sys

origen, destino = sys.argv[1], sys.argv[2]
a, b = sqlite3.connect(origen), sqlite3.connect(destino)
a.backup(b)
estado = b.execute("PRAGMA integrity_check").fetchone()[0]
a.close()
b.close()
print(f"Respaldo en {destino}: integrity_check = {estado}")
sys.exit(0 if estado == "ok" else 1)
