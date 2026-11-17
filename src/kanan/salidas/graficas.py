"""Gráficas de evolución, frente de Pareto y comparación de métodos."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from kanan.optimizacion.aptitud import ETIQUETAS, OBJETIVOS
from kanan.optimizacion.nsga2 import Historial
from kanan.salidas import estilo
from kanan.validacion.comparacion import ResultadoMetodo


def figura_evolucion(historial: Historial, ruta: Path) -> None:
    """Mejor valor y promedio de cada objetivo por generación (un panel por objetivo)."""
    estilo.aplicar()
    mejor, promedio = historial.mejor(), historial.promedio()
    generaciones = np.arange(len(mejor))
    figura, ejes = plt.subplots(2, 2, figsize=(10, 6.2), sharex=True)
    for m, (ax, objetivo) in enumerate(zip(ejes.ravel(), OBJETIVOS, strict=True)):
        ax.plot(generaciones, promedio[:, m], color=estilo.REFERENCIA, label="Promedio")
        ax.plot(generaciones, mejor[:, m], color=estilo.SERIE_1, label="Mejor")
        ax.set_title(ETIQUETAS[objetivo])
        ax.set_ylim(bottom=0)
    for ax in ejes[1]:
        ax.set_xlabel("Generación")
    ejes[0, 0].legend(loc="lower left")
    figura.suptitle("Evolución de la aptitud (escenarios de entrenamiento)", x=0.07, ha="left",
                    fontsize=12, fontweight="bold", color=estilo.TINTA)  # fmt: skip
    figura.tight_layout()
    estilo.guardar(figura, ruta)


def figura_hipervolumen(valores: np.ndarray, ruta: Path) -> None:
    estilo.aplicar()
    figura, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(np.arange(len(valores)), valores, color=estilo.SERIE_1)
    ax.annotate(f"{valores[-1]:.3f}", (len(valores) - 1, valores[-1]), xytext=(4, 0),
                textcoords="offset points", va="center", color=estilo.TINTA_SECUNDARIA)  # fmt: skip
    ax.set_title("Hipervolumen del frente de Pareto por generación")
    ax.set_xlabel("Generación")
    ax.set_ylabel("Fracción dominada de la caja de referencia")
    ax.set_ylim(bottom=0)
    estilo.guardar(figura, ruta)


def figura_pareto(frente: np.ndarray, elegidos: dict[str, tuple[int, str]], ruta: Path) -> None:
    """Frente de Pareto en los seis pares de ejes.

    ``elegidos`` asigna a cada etiqueta el índice del plan en el frente y su color.
    """
    estilo.aplicar()
    figura, ejes = plt.subplots(2, 3, figsize=(12, 7))
    for ax, (i, j) in zip(ejes.ravel(), combinations(range(len(OBJETIVOS)), 2), strict=True):
        ax.scatter(frente[:, i], frente[:, j], s=16, color=estilo.REFERENCIA, linewidths=0,
                   label="Frente de Pareto")  # fmt: skip
        for etiqueta, (indice, color) in elegidos.items():
            ax.scatter(frente[indice, i], frente[indice, j], s=90, color=color, zorder=3,
                       edgecolors=estilo.SUPERFICIE, linewidths=2, label=etiqueta)  # fmt: skip
        ax.set_xlabel(ETIQUETAS[OBJETIVOS[i]])
        ax.set_ylabel(ETIQUETAS[OBJETIVOS[j]])
    manijas, etiquetas = ejes[0, 0].get_legend_handles_labels()
    figura.legend(manijas, etiquetas, loc="upper right", ncol=len(etiquetas))
    figura.suptitle(f"Frente de Pareto · {len(frente)} planes no dominados", x=0.05, ha="left",
                    fontsize=12, fontweight="bold", color=estilo.TINTA)  # fmt: skip
    figura.tight_layout(rect=(0, 0, 1, 0.95))
    estilo.guardar(figura, ruta)


def _colores(resultados: list[ResultadoMetodo]) -> list[str]:
    planes = iter(estilo.COLORES_PLANES)
    return [next(planes, estilo.SERIE_1) if r.es_kanan else estilo.REFERENCIA for r in resultados]


def figura_comparacion(resultados: list[ResultadoMetodo], ruta: Path) -> None:
    """Área quemada media de cada método en los escenarios de prueba."""
    estilo.aplicar()
    figura, ax = plt.subplots(figsize=(8.4, 0.5 * len(resultados) + 1.4))
    nombres = [r.nombre for r in resultados]
    medias = [r.area_media for r in resultados]
    barras = ax.barh(nombres, medias, color=_colores(resultados), height=0.62)
    ax.bar_label(barras, labels=[f"{m:,.0f} ha" for m in medias], padding=4,
                 color=estilo.TINTA_SECUNDARIA, fontsize=8)  # fmt: skip
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(medias) * 1.15)
    ax.set_xlabel("Área quemada media (ha)")
    ax.set_title("Área quemada por método · escenarios de prueba, mismo presupuesto")
    ax.tick_params(axis="y", labelsize=9, labelcolor=estilo.TINTA)
    estilo.guardar(figura, ruta)


def figura_cajas(resultados: list[ResultadoMetodo], ruta: Path) -> None:
    """Diagrama de caja del área quemada por escenario de prueba."""
    estilo.aplicar()
    figura, ax = plt.subplots(figsize=(8.4, 0.55 * len(resultados) + 1.4))
    cajas = ax.boxplot(
        [r.area_por_escenario for r in resultados],
        orientation="horizontal",
        tick_labels=[r.nombre for r in resultados],
        patch_artist=True,
        widths=0.6,
        medianprops={"color": estilo.TINTA, "linewidth": 1.6},
        whiskerprops={"color": estilo.TINTA_TENUE},
        capprops={"color": estilo.TINTA_TENUE},
        flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": estilo.TINTA_TENUE,
                    "markeredgewidth": 0},
    )  # fmt: skip
    for caja, color in zip(cajas["boxes"], _colores(resultados), strict=True):
        caja.set(facecolor=color, edgecolor=estilo.SUPERFICIE)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlim(left=0)
    ax.set_xlabel("Área quemada por escenario (ha)")
    ax.set_title("Dispersión del área quemada · escenarios de prueba")
    ax.tick_params(axis="y", labelsize=9, labelcolor=estilo.TINTA)
    estilo.guardar(figura, ruta)
