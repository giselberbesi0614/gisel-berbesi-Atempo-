#!/usr/bin/env bash
# Healthcheck posterior al despliegue: consulta /salud hasta que responda estado "ok".
# Uso: scripts/healthcheck.sh https://mi-app.onrender.com [intentos] [segundos_entre_intentos]
set -u
URL="${1:?Falta la URL base}"; INTENTOS="${2:-12}"; ESPERA="${3:-10}"
for i in $(seq 1 "$INTENTOS"); do
  CUERPO=$(curl -fsS --max-time 10 "${URL%/}/salud" 2>/dev/null) && \
  echo "$CUERPO" | grep -q '"estado":"ok"' && { echo "OK en el intento $i: $CUERPO"; exit 0; }
  echo "Intento $i/$INTENTOS sin respuesta correcta; espero ${ESPERA}s"; sleep "$ESPERA"
done
echo "FALLO: $URL/salud no respondió estado ok tras $INTENTOS intentos" >&2
exit 1
