"""Complejidad ciclomática aproximada (McCabe) por función con ast. Uso: python scripts/complejidad.py [umbral]"""
import ast
import glob
import sys

umbral = int(sys.argv[1]) if len(sys.argv) > 1 else 10
filas = []
for f in sorted(glob.glob("atempo/**/*.py", recursive=True)):
    for n in ast.walk(ast.parse(open(f, encoding="utf-8").read())):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            c = 1
            for x in ast.walk(n):
                if isinstance(x, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp)):
                    c += 1
                elif isinstance(x, ast.comprehension):
                    c += 1 + len(x.ifs)
                elif isinstance(x, ast.BoolOp):
                    c += len(x.values) - 1
            filas.append((c, f, n.lineno, n.name))
filas.sort(reverse=True)
for c, f, ln, nombre in filas[:8]:
    print(f"{c:3d}  {f}:{ln}  {nombre}{'   <-- supera ' + str(umbral) if c > umbral else ''}")
print("funciones sobre el umbral:", sum(1 for c, *_ in filas if c > umbral), "de", len(filas))
