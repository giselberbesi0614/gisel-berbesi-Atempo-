# Postmortem (simulado y sin culpables): base SQLite dañada

**Tipo:** incidente SIMULADO. Los tiempos de máquina se midieron en un simulacro; los tiempos humanos son estimaciones.
**Impacto simulado:** el servicio devuelve error 500 en todas las rutas durante la ventana del incidente; no hay pérdida de datos personales (RN-06).

## Resumen
Un reinicio forzado del servidor durante una escritura dejó el archivo SQLite dañado. Al arrancar, la aplicación lanzó `DatabaseError: database disk image is malformed` y no atendió peticiones.

## Cronología (simulada)
| Momento | Evento | Fuente |
|---|---|---|
| T0 | Reinicio forzado durante una escritura; el archivo queda dañado | Simulado (se truncó el archivo a 100 bytes) |
| T0 + 5 min | `/salud` deja de responder; se cumple la condición de alerta | Estimado |
| T0 + 10 min | Se abre el runbook; `integrity_check` confirma el daño (error inmediato) | Medido: detección inmediata |
| T0 + 15 min | Se restaura el respaldo y se reinicia | Medido: 9 ms de restauración y arranque; la espera es humana |
| T0 + 20 min | `/salud` vuelve a responder `ok`; 5 materias recuperadas de 5 | Medido |

Duración estimada del incidente: **20 minutos**, del orden de lo que consume un SLO del 99,95 % en un mes (21,6 min).

## Causa raíz (de proceso, no de persona)
1. **No había respaldos automáticos:** el respaldo del simulacro se hizo a mano, justo antes de dañar la base. Sin ese paso, la única opción era recrear la base vacía.
2. **No había alerta automática:** el aviso dependía de que alguien notara el error.
3. **El runbook no existía** hasta esta guía y la restauración nunca se había probado.
4. **Una sola persona operadora:** no hay segunda revisión ni relevo.
5. **Escritura directa al archivo sin copia de seguridad previa en el despliegue.**

## Qué funcionó
- La detección con `PRAGMA integrity_check` es inmediata y clara.
- La restauración desde un respaldo es muy rápida y conserva los datos.
- El healthcheck del pipeline confirma la recuperación.

## Acciones preventivas
| Acción | Responsable | Plazo |
|---|---|---|
| Respaldo automático diario con `scripts/respaldar.py` | Gisel | Antes del primer despliegue con volumen |
| Alerta sobre `/salud` y la tasa de 5xx (Grafana o proveedor) | Gisel | Con el dashboard de la Guía 13 |
| Probar la restauración una vez al mes y anotarlo | Gisel | Mensual |
| Revisar si SQLite es adecuado si hay usuarios reales (ADR 03) | Gisel | Antes de datos reales |
