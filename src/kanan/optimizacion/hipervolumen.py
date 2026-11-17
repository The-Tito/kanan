"""Hipervolumen del frente de Pareto, estimado por Monte Carlo."""

from __future__ import annotations

import numpy as np

from kanan.optimizacion.nsga2 import Historial

MUESTRAS = 20_000


def hipervolumen(
    frente: np.ndarray, ideal: np.ndarray, referencia: np.ndarray, muestras: np.ndarray
) -> float:
    """Fracción de la caja [ideal, referencia] dominada por ``frente`` (minimización).

    ``muestras`` son puntos uniformes en el cubo unitario; usar siempre los mismos hace
    comparables los valores entre generaciones.
    """
    amplitud = np.where(referencia > ideal, referencia - ideal, 1.0)
    normalizado = (frente - ideal) / amplitud
    normalizado = normalizado[(normalizado < 1.0).all(axis=1)]
    if normalizado.size == 0:
        return 0.0
    dominada = np.zeros(len(muestras), dtype=bool)
    for punto in normalizado:
        dominada |= (muestras >= punto).all(axis=1)
    return float(dominada.mean())


def hipervolumen_por_generacion(historial: Historial, semilla: int = 0) -> np.ndarray:
    """Hipervolumen del frente factible de cada generación, con una caja común.

    El punto ideal es el mínimo observado en toda la corrida y el de referencia es el peor
    valor de la población inicial, así que la curva mide el avance respecto al arranque.
    """
    factible = historial.violacion <= 0
    objetivos = np.where(factible[:, :, None], historial.objetivos, np.nan)
    ideal = np.nanmin(objetivos, axis=(0, 1))
    referencia = np.nanmax(objetivos[0], axis=0)
    muestras = np.random.default_rng(semilla).random((MUESTRAS, objetivos.shape[2]))
    return np.array(
        [
            hipervolumen(historial.frente(g), ideal, referencia, muestras)
            for g in range(len(historial.objetivos))
        ]
    )
