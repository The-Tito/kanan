"""Elección de los tres planes que se presentan, a partir del frente de Pareto."""

from __future__ import annotations

import numpy as np

from kanan.optimizacion.aptitud import AREA, COSTO, IMPACTO

MENOR_AREA = "menor_area"
MENOR_COSTO = "menor_costo_impacto"
EQUILIBRADO = "equilibrado"

FRACCION_REDUCCION = 0.25
"""Parte de la mejor reducción de área que debe lograr el plan de menor costo."""

NOMBRES = {
    MENOR_AREA: "Menor área quemada",
    MENOR_COSTO: "Menor costo e impacto",
    EQUILIBRADO: "Más equilibrado",
}


def normalizar(objetivos: np.ndarray) -> np.ndarray:
    """Escala cada objetivo a [0, 1] dentro del frente."""
    minimo, maximo = objetivos.min(axis=0), objetivos.max(axis=0)
    return (objetivos - minimo) / np.where(maximo > minimo, maximo - minimo, 1.0)


def elegir_planes(objetivos: np.ndarray) -> dict[str, int]:
    """Índices, dentro del frente, de los tres planes representativos.

    - Menor área quemada.
    - Menor costo e impacto: mínima suma de ambos objetivos normalizados, entre los planes
      que logran al menos una cuarta parte de la mejor reducción de área del frente. Sin ese
      piso el elegido sería siempre "no construir nada", que es el extremo barato del frente.
    - Más equilibrado: el más cercano al punto ideal con los cuatro objetivos normalizados,
      distinto de los dos anteriores y nunca más barato que el de menor costo, para que los
      tres queden ordenados de más protección a menos gasto.
    """
    norm = normalizar(objetivos)
    menor_area = int(np.lexsort((objetivos[:, COSTO], objetivos[:, AREA]))[0])
    gasto = norm[:, COSTO] + norm[:, IMPACTO]
    gasto[norm[:, AREA] > 1.0 - FRACCION_REDUCCION] = np.inf
    menor_costo = int(np.argmin(gasto))
    distancia = np.linalg.norm(norm, axis=1)
    intermedios = np.ones(len(objetivos), dtype=bool)
    intermedios[[menor_area, menor_costo]] = False
    intermedios &= gasto >= gasto[menor_costo]
    if intermedios.any():
        distancia[~intermedios] = np.inf
    return {
        MENOR_AREA: menor_area,
        MENOR_COSTO: menor_costo,
        EQUILIBRADO: int(np.argmin(distancia)),
    }
