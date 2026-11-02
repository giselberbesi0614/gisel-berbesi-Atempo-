# Runbook: Atempo no responde o la base SQLite está dañada

**Responsable:** Gisel Ximena Berbesi Moreno (única integrante). No hay guardia ni escalamiento; Atempo no promete disponibilidad (RNF-07).
**Alerta que lo activa:** `/salud` no responde `{"estado":"ok"}` durante 5 minutos, o más del 5 % de las peticiones terminan en 5xx.
**Estado de verificación:** cada paso indica si lo ejecuté ([verificado]) o si depende de herramientas que no pude usar ([no probado]).

## 1. Confirmar el problema
```
scripts/healthcheck.sh https://<URL-PUBLICA> 3 5
```
[verificado en local: con el servidor arriba sale con código 0; caído, con código 1 tras los reintentos]. Si responde ok, el problema es intermitente: seguir en el paso 2 para buscar errores.

## 2. Buscar la causa en los logs
- Cada petición deja una línea JSON con `trace_id`, `ruta`, `estado` y `duracion_ms`. Buscar las líneas con `"estado": 5xx` y leer el mensaje de error de la salida de la aplicación en ese instante.
- Local con Docker: `docker compose logs --tail=100 atempo` [no probado: sin servicio de Docker]. En Render: pestaña «Logs» del servicio.
- Si aparece `database disk image is malformed` o `file is not a database`, ir al paso 4.

## 3. Si el problema empezó tras un despliegue
Volver al despliegue anterior sano desde el panel de la plataforma [no probado] y repetir el paso 1. Abrir un Pull Request con la corrección antes de volver a desplegar.

## 4. Base de datos dañada
1. Comprobar la base:
   ```
   python -c "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute('PRAGMA integrity_check').fetchone()[0])" /data/atempo.db
   ```
   [verificado] Con una base sana imprime `ok`; con una dañada lanza `DatabaseError: database disk image is malformed`.
2. Si existe un respaldo bueno: detener el servicio, copiar el respaldo sobre `/data/atempo.db` y reiniciar [verificado en local: restauración y arranque en 9 ms, con las mismas 5 materias].
3. Si no hay respaldo: borrar `/data/atempo.db` y reiniciar; Atempo crea una base nueva con datos de demostración. Se pierden las sesiones (son anónimas y sin datos personales, RN-06).
4. Confirmar con el paso 1.

## 5. Después del incidente
Escribir el postmortem (sin culpables) en `docs/` el mismo día y abrir una tarea por cada acción preventiva.

## Mantenimiento (prevención)
- Respaldo: `python scripts/respaldar.py /data/atempo.db /data/respaldo.db` [verificado: termina con `integrity_check = ok` y código 0; usa la API de respaldo de SQLite, segura con la base en uso].
- Nota: en el plan gratuito de Render el disco es efímero; allí los datos se pierden en cada despliegue y este runbook solo aplica a un hosting con volumen.
