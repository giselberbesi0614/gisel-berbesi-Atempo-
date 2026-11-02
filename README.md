# Atempo

Plataforma web para gestionar y analizar la carga académica de estudiantes de la Universidad de Pamplona (MVP con datos de demostración).

## Arquitectura (monolito modular en capas)
```
web (Flask: rutas /api/v1 + interfaz) → servicios (Dashboard) → dominio (reglas) → datos (FuenteDeDatos / sesiones en memoria)
```
- `atempo/dominio`: modelos inmutables, `CalculadoraDeCarga`, `priorizador`, reglas RN-01…RN-07. No depende de Flask.
- `atempo/datos`: contrato `FuenteDeDatos` (DIP) y `SesionDemo` (datos ficticios por visitante, TTL 60 min, con lock).
- `atempo/servicios`: `Dashboard` arma el resumen y los mensajes.
- `atempo/web`: API REST y la interfaz (diseño de Figma).

## Ejecutar
```
pip install -r requirements.txt
flask --app wsgi run
gunicorn wsgi:app --workers 1 --threads 8   # un solo proceso: las sesiones viven en memoria
```
## Persistencia (opcional)
Por defecto los datos de demostración viven en memoria. Para guardarlos en SQLite define la variable `ATEMPO_DB`:
```
set ATEMPO_DB=atempo.db        # Windows (cmd)      $env:ATEMPO_DB="atempo.db"   # PowerShell
flask --app wsgi run
```
El esquema está versionado (`PRAGMA user_version`) y se migra solo al arrancar. Datos siempre ficticios (RN-06).

## Pruebas y calidad
```
python -m unittest discover -s tests
pip install -r requirements-dev.txt
flake8 atempo tests wsgi.py
coverage run --source=atempo/dominio -m unittest discover -s tests && coverage report --fail-under=80
```
## Reglas clave
Carga = horas pendientes ÷ horas disponibles × 100. Baja < 50 %, Media 50–80 %, Alta > 80 %. Sin horas disponibles no se calcula. Las completadas no cuentan. Semana de lunes a domingo. Solo datos ficticios (Ley 1581 de 2012).
