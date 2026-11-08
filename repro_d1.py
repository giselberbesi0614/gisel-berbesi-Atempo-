from datetime import date
from atempo.dominio.modelos import Actividad
from atempo.dominio.calculadora import CalculadoraDeCarga, porcentaje_para_mostrar

F = date(2026, 11, 15)
calc = CalculadoraDeCarga()
a = Actividad(1, "Informe", F, 2.0, False, 1)
b = Actividad(2, "Taller", F, 16.1, False, 1)
for e, acts in (("antes", [a, b]), ("despues", [Actividad(1, "Informe", F, 2.0, True, 1), b])):
    r = calc.calcular(acts, 20)
    print(e, r.nivel.value, r.porcentaje, round(r.porcentaje), porcentaje_para_mostrar(r.nivel, r.porcentaje))

mal = bien = 0
for i in range(0, 20001):
    p = i / 100
    n = calc._clasificar(p)
    def coh(v):
        return (v < 50) if n.value == "Baja" else (50 <= v <= 80) if n.value == "Media" else (v > 80)
    mal += not coh(round(p)); bien += not coh(porcentaje_para_mostrar(n, p))
print("incoherencias con round():", mal, "| con porcentaje_para_mostrar:", bien)
