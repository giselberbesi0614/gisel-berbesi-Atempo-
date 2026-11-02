import logging

from atempo.web import crear_app

logging.basicConfig(level=logging.INFO, format="%(message)s")   # las líneas JSON de telemetría salen por stdout/stderr
app = crear_app()
