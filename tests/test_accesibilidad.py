"""RNF-08: el nivel se comunica con texto ademas de color y el contraste cumple WCAG 2.2 AA (4.5:1 en texto)."""
import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "atempo" / "web" / "static"


def _lum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contraste(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class TestContraste(unittest.TestCase):
    def test_indicadores_de_nivel(self):
        js = (STATIC / "atempo.js").read_text(encoding="utf-8")
        pares = re.findall(r"(Baja|Media|Alta):\{c:\"(#\w{6})\",bg:\"(#\w{6})\"\}", js)
        self.assertEqual(len(pares), 3)
        for nombre, fg, bg in pares:
            self.assertGreaterEqual(contraste(fg, bg), 4.5, nombre)

    def test_textos_secundarios(self):
        css = (STATIC / "atempo.css").read_text(encoding="utf-8")
        gris = re.search(r"--muted:(#\w{6})", css).group(1)
        for fondo in ("#ffffff", "#f6f7fb", "#f8f8fb"):
            self.assertGreaterEqual(contraste(gris, fondo), 4.5, fondo)

    def test_boton_primario(self):
        self.assertGreaterEqual(contraste("#ffffff", "#6656d9"), 4.5)

    def test_nivel_tambien_en_texto(self):
        js = (STATIC / "atempo.js").read_text(encoding="utf-8")
        self.assertIn("c.nivel || \"Sin datos\"", js)     # la etiqueta del nivel es texto, no solo color


if __name__ == "__main__":
    unittest.main()
