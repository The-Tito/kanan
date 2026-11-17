"""Mapas: área de estudio, planes de brechas, probabilidad de quema y animación."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import ListedColormap, to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from kanan.dominio import catalogos as cat
from kanan.dominio.mapa import Mapa
from kanan.dominio.plan import ANGULO, LONGITUD, X, Y
from kanan.salidas import estilo

CUADROS_POR_SEGUNDO = 6


def _extension_km(mapa: Mapa) -> tuple[float, float, float, float]:
    return (0.0, mapa.ancho_m / 1000.0, mapa.alto_m / 1000.0, 0.0)


def dibujar_fondo(ax, mapa: Mapa, alfa: float = 1.0) -> None:
    """Vegetación, relieve, caminos, zona núcleo y poblados."""
    colores = ListedColormap([v.color for v in cat.VEGETACION])
    extension = _extension_km(mapa)
    ax.imshow(mapa.vegetacion, cmap=colores, vmin=-0.5, vmax=len(cat.VEGETACION) - 0.5,
              extent=extension, interpolation="nearest", alpha=alfa)  # fmt: skip
    km_x = (np.arange(mapa.forma[1]) + 0.5) * mapa.tam_celda_m / 1000.0
    km_y = (np.arange(mapa.forma[0]) + 0.5) * mapa.tam_celda_m / 1000.0
    ax.contour(km_x, km_y, mapa.elevacion, levels=8, colors="#00000030", linewidths=0.5)
    nucleo = (mapa.zona_valor == cat.Z_NUCLEO).astype(float)
    ax.contour(km_x, km_y, nucleo, levels=[0.5], linewidths=1.4, linestyles="--",
               colors=cat.ZONAS_VALOR[cat.Z_NUCLEO].color)  # fmt: skip
    filas, cols = np.nonzero(mapa.caminos)
    ax.scatter(km_x[cols], km_y[filas], s=3, color="#6b4f3a", marker="s", linewidths=0)
    filas, cols = np.nonzero(mapa.zona_valor == cat.Z_INFRAESTRUCTURA)
    ax.scatter(km_x[cols], km_y[filas], s=40, marker="^", zorder=4, edgecolors="white",
               color=cat.ZONAS_VALOR[cat.Z_INFRAESTRUCTURA].color, linewidths=0.8)  # fmt: skip
    ax.set_xlim(extension[0], extension[1])
    ax.set_ylim(extension[2], extension[3])
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xlabel("km (oeste → este)")
    ax.set_ylabel("km (norte → sur)")


def dibujar_brechas(ax, brechas: np.ndarray, numerar: bool = True) -> None:
    """Cada brecha como segmento negro con borde blanco, numerada en su inicio."""
    for k, brecha in enumerate(brechas):
        angulo = np.radians(brecha[ANGULO])
        x0, y0 = brecha[X] / 1000.0, brecha[Y] / 1000.0
        x1 = x0 + np.cos(angulo) * brecha[LONGITUD] / 1000.0
        y1 = y0 + np.sin(angulo) * brecha[LONGITUD] / 1000.0
        ax.plot([x0, x1], [y0, y1], color="white", linewidth=4.5, solid_capstyle="round", zorder=5)
        ax.plot([x0, x1], [y0, y1], color=estilo.COLOR_BRECHA, linewidth=2.2,
                solid_capstyle="round", zorder=6)  # fmt: skip
        if numerar:
            ax.annotate(str(k + 1), ((x0 + x1) / 2, (y0 + y1) / 2), fontsize=7, zorder=7,
                        ha="center", va="center", color=estilo.TINTA, annotation_clip=True,
                        bbox={"boxstyle": "circle,pad=0.15", "fc": "white", "ec": estilo.TINTA,
                              "lw": 0.6})  # fmt: skip


def _leyenda_mapa(con_brechas: bool) -> list:
    elementos = [Patch(facecolor=v.color, label=v.nombre) for v in cat.VEGETACION]
    elementos += [
        Line2D([], [], color="#6b4f3a", linestyle=":", linewidth=2, label="Camino"),
        Line2D([], [], color=cat.ZONAS_VALOR[cat.Z_NUCLEO].color, linestyle="--", linewidth=1.4,
               label="Zona núcleo"),  # fmt: skip
        Line2D([], [], color=cat.ZONAS_VALOR[cat.Z_INFRAESTRUCTURA].color, marker="^",
               linestyle="", label="Infraestructura"),  # fmt: skip
    ]
    if con_brechas:
        elementos.append(Line2D([], [], color=estilo.COLOR_BRECHA, linewidth=2.2, label="Brecha"))
    return elementos


def figura_mapa(mapa: Mapa, ruta: Path, brechas: np.ndarray | None = None,
                titulo: str = "Área de estudio (mapa sintético)") -> None:  # fmt: skip
    estilo.aplicar()
    figura, ax = plt.subplots(figsize=(8.2, 6.2))
    dibujar_fondo(ax, mapa)
    if brechas is not None:
        dibujar_brechas(ax, brechas)
    ax.set_title(titulo)
    ax.legend(handles=_leyenda_mapa(brechas is not None), loc="center left",
              bbox_to_anchor=(1.02, 0.5))  # fmt: skip
    return estilo.guardar(figura, ruta)


def figura_riesgo(mapa: Mapa, ruta: Path | None = None):
    """Probabilidad de ignición de la base de conocimiento."""
    estilo.aplicar()
    figura, ax = plt.subplots(figsize=(6.6, 5.4))
    relativa = mapa.prob_ignicion / mapa.prob_ignicion.max()
    imagen = ax.imshow(relativa, cmap=estilo.MAPA_PROBABILIDAD, extent=_extension_km(mapa),
                       vmin=0, vmax=1, interpolation="nearest")  # fmt: skip
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xlabel("km (oeste → este)")
    ax.set_ylabel("km (norte → sur)")
    ax.set_title("Riesgo de ignición (relativo al máximo)")
    figura.colorbar(imagen, ax=ax, fraction=0.046, pad=0.03)
    return estilo.guardar(figura, ruta)


def figura_probabilidad(mapa: Mapa, sin_brechas: np.ndarray, con_brechas: np.ndarray,
                        brechas: np.ndarray, titulo: str, ruta: Path | None = None):  # fmt: skip
    """Fracción de escenarios en que arde cada celda, sin y con el plan."""
    estilo.aplicar()
    figura, ejes = plt.subplots(1, 2, figsize=(11, 4.9), sharey=True)
    maximo = max(float(sin_brechas.max()), 1e-9)
    paneles = (("Sin brechas", sin_brechas, None), ("Con el plan", con_brechas, brechas))
    for ax, (nombre, probabilidad, plan) in zip(ejes, paneles, strict=True):
        imagen = ax.imshow(probabilidad, cmap=estilo.MAPA_PROBABILIDAD, vmin=0, vmax=maximo,
                           extent=_extension_km(mapa), interpolation="nearest")  # fmt: skip
        if plan is not None:
            dibujar_brechas(ax, plan, numerar=False)
        ax.set_xlim(0, mapa.ancho_m / 1000.0)
        ax.set_ylim(mapa.alto_m / 1000.0, 0)
        ax.set_aspect("equal")
        ax.grid(False)
        ax.set_title(f"{nombre} · media {probabilidad.mean():.1%} del mapa")
        ax.set_xlabel("km (oeste → este)")
    ejes[0].set_ylabel("km (norte → sur)")
    figura.suptitle(titulo, x=0.07, ha="left", fontsize=12, fontweight="bold", color=estilo.TINTA)
    figura.colorbar(imagen, ax=ejes, fraction=0.025, pad=0.02, label="Probabilidad de quema")
    return estilo.guardar(figura, ruta)


def _capa_fuego(t_ignicion: np.ndarray, paso: int) -> np.ndarray:
    """Imagen RGBA: transparente sin arder, rojo en llamas, gris oscuro ya quemado."""
    capa = np.zeros((*t_ignicion.shape, 4))
    capa[(t_ignicion >= 0) & (t_ignicion < paso)] = to_rgba(estilo.COLOR_QUEMADO, 0.92)
    capa[t_ignicion == paso] = to_rgba(estilo.COLOR_LLAMAS)
    return capa


def animar_incendio(mapa: Mapa, t_sin: np.ndarray, t_con: np.ndarray, brechas: np.ndarray,
                    titulo: str, ruta: Path) -> None:  # fmt: skip
    """GIF del mismo incendio sin brechas (izquierda) y con el plan (derecha)."""
    estilo.aplicar()
    figura, ejes = plt.subplots(1, 2, figsize=(9.6, 4.9), sharey=True)
    capas, textos = [], []
    for ax, (nombre, plan) in zip(ejes, (("Sin brechas", None), ("Con el plan", brechas)),
                                  strict=True):  # fmt: skip
        dibujar_fondo(ax, mapa, alfa=0.75)
        if plan is not None:
            dibujar_brechas(ax, plan, numerar=False)
        capas.append(ax.imshow(_capa_fuego(t_sin, 0), extent=_extension_km(mapa),
                               interpolation="nearest", zorder=3))  # fmt: skip
        textos.append(ax.set_title(nombre))
    ejes[1].set_ylabel("")
    figura.suptitle(titulo, x=0.07, ha="left", fontsize=11, fontweight="bold", color=estilo.TINTA)
    hectareas = mapa.area_celda_ha
    ultimo = int(max(t_sin.max(), t_con.max())) + 1

    def actualizar(paso: int):
        nombres = ("Sin brechas", "Con el plan")
        for capa, texto, tiempos, nombre in zip(capas, textos, (t_sin, t_con), nombres,
                                                strict=True):  # fmt: skip
            capa.set_data(_capa_fuego(tiempos, paso))
            quemado = ((tiempos >= 0) & (tiempos <= paso)).sum() * hectareas
            texto.set_text(f"{nombre} · paso {paso} · {quemado:,.0f} ha")
        return capas

    cuadros = list(range(ultimo + 1)) + [ultimo] * CUADROS_POR_SEGUNDO
    animacion = FuncAnimation(figura, actualizar, frames=cuadros, blit=False)
    animacion.save(ruta, writer=PillowWriter(fps=CUADROS_POR_SEGUNDO), dpi=72)
    plt.close(figura)
