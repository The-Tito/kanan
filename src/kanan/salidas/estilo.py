"""Estilo común de las figuras.

Colores categóricos en orden fijo (azul, naranja, aqua), tomados de una paleta validada para
daltonismo. El color sigue a la entidad: cada plan de Kanan conserva el suyo en todas las
figuras, y los métodos de referencia van en gris.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"

SERIE_1, SERIE_2, SERIE_3 = "#2a78d6", "#eb6834", "#1baf7a"
COLORES_PLANES = (SERIE_1, SERIE_2, SERIE_3)
REFERENCIA = "#b4b2aa"

COLOR_BRECHA = "#0b0b0b"
COLOR_LLAMAS = "#e34948"
COLOR_QUEMADO = "#3a3836"
MAPA_PROBABILIDAD = "Oranges"

DPI = 130


def aplicar() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SUPERFICIE,
            "axes.facecolor": SUPERFICIE,
            "savefig.facecolor": SUPERFICIE,
            "axes.edgecolor": EJE,
            "axes.labelcolor": TINTA_SECUNDARIA,
            "axes.titlecolor": TINTA,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": REJILLA,
            "grid.linewidth": 0.6,
            "xtick.color": TINTA_TENUE,
            "ytick.color": TINTA_TENUE,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.frameon": False,
            "legend.fontsize": 8,
            "font.size": 9,
            "lines.linewidth": 2.0,
        }
    )


def guardar(figura, ruta) -> None:
    figura.savefig(ruta, dpi=DPI, bbox_inches="tight")
    plt.close(figura)
