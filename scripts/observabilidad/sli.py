"""Calcula los SLI de Atempo a partir del texto de /metrics.
Uso: python observabilidad/sli.py ejemplo_metrics.txt"""
import re
import sys

t = open(sys.argv[1], encoding="utf-8").read()
reqs = [(m, r, int(e), int(n)) for m, r, e, n in
        re.findall(r'atempo_http_requests_total\{method="(\w+)",route="([^"]+)",status="(\d+)"\} (\d+)', t)]
total = sum(n for *_, n in reqs)
malas = sum(n for _, _, e, n in reqs if e >= 500)
print(f"SLI de disponibilidad: {100 * (total - malas) / total:.3f} %  ({total - malas} de {total} peticiones sin error 5xx)")
b = {l: int(n) for l, n in re.findall(r'route="/api/v1/estado",le="([^"]+)"\} (\d+)', t)}
N = b["+Inf"]
for lim in ("100", "250", "500"):
    print(f"SLI de latencia (/estado ≤ {lim} ms): {100 * b[lim] / N:.2f} %  ({b[lim]} de {N})")
