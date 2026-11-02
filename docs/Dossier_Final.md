# Dossier Técnico Final — Atempo (FPI-32)

Autora: Gisel Ximena Berbesi Moreno · Universidad de Pamplona · Ingeniería de Software II · 1 de noviembre de 2026

Regla de este dossier: solo se afirma lo que se puede comprobar en el repositorio. Lo que no se pudo ejecutar se dice.

## 1. Qué es Atempo
Aplicación web (Flask 3, Python) que calcula la carga académica semanal de un estudiante (Baja < 50 %, Media, Alta > 80 %) y recomienda qué actividades hacer primero. Datos de demostración, sin cuentas ni datos personales (RN-06).

## 2. Verificación (¿lo construimos bien?) — con evidencia
| Afirmación | Evidencia | Cómo se comprueba |
|---|---|---|
| 89 pruebas pasan | `tests/` | `python -m unittest discover -s tests -t .` |
| Contrato OpenAPI y API coinciden | `docs/openapi.yaml`, `tests/test_contrato.py` | misma orden |
| Refactor de `Dashboard.resumen` sin cambio de comportamiento | `tests/test_resumen_equivalencia.py`, `tests/golden_resumen.json` | misma orden |
| Ninguna función con complejidad McCabe > 10 | `scripts/complejidad.py` | `python scripts/complejidad.py 10` |
| Rendimiento local: p95 de /estado 78,5 ms, 0 % errores, 3.935 peticiones | `pruebas_carga/resultado_k6.txt` | `k6 run pruebas_carga/carga_estado.js` (solo localhost) |
| Telemetría sin PII, /metrics apagado por defecto | `atempo/web/telemetria.py`, `tests/test_telemetria.py` | pruebas |
| Recuperación de base dañada | `docs/Runbook_base_de_datos.md`, `scripts/respaldar.py` | simulacro descrito en el postmortem |

## 3. Validación (¿construimos lo correcto?)
**No hay validación empírica.** Atempo no tiene usuarios reales ni producción. Lo que existe es verificación contra el ERS. Validar requiere que estudiantes la usen durante un periodo y se midan resultados.

## 4. Lo que está escrito pero NO se ha ejecutado
- Flujos `.github/workflows/ci.yml`, `deploy.yml`, `ci-security.yml` (nunca corrieron en GitHub).
- `Dockerfile` y `docker-compose*.yml` (imagen nunca construida).
- Despliegue en Render (el servicio no existe).
- Semgrep, Trivy, SonarQube, flake8, coverage (no instalables en el entorno de trabajo).
- Dashboard de Grafana.

Por eso no se afirma «0 vulnerabilidades críticas», ni cobertura actual, ni disponibilidad en producción.

## 5. Decisiones (ADR 01 a 15)
01 línea base v0.2.0 y deuda por riesgo · 02 drivers · 03 SQLite opcional · 04 monolito modular en capas · 05 sin distribuir contextos · 06 API sin autenticación declarada · 07 estrategia de pruebas · 08 aceptar rendimiento · 09 CI en tres jobs · 10 imagen no root · 11 CD con healthcheck · 12 DevSecOps · 13 telemetría propia · 14 SLO 99 % / 95 % ≤ 500 ms · 15 deuda por riesgo y roadmap.

## 6. Deuda técnica residual y roadmap
Hito 1 (nov.–dic. 2026): subir todo, ejecutar CI, construir Docker, desplegar con HTTPS. Hito 2 (ene.–feb. 2027): datos persistentes, respaldo, unificar el CRUD. Hito 3 (mar.–abr. 2027): cuentas, idempotencia, avisos.

## 7. Uso de IA (FPI-17 a FPI-31)
6 errores verificados en salidas de IA y 4 errores propios detectados al auditar. Las FPI-01 a FPI-16 no están contabilizadas aquí.
