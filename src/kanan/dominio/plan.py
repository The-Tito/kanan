"""Plan de brechas: del cromosoma a las celdas desmontadas, su costo y su impacto.

Un plan son K brechas y cada brecha 4 genes reales: ``x`` e ``y`` de inicio en metros,
``angulo`` en grados y ``longitud`` en metros. El ángulo se mide desde el este y crece hacia
el sur (0° = este, 90° = sur), igual que las filas de la cuadrícula.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit, prange

from kanan.config import ConfigBrechas
from kanan.dominio import catalogos as cat
from kanan.dominio.mapa import Mapa
from kanan.paralelo import CANDADO

GENES_POR_BRECHA = 4
X, Y, ANGULO, LONGITUD = range(GENES_POR_BRECHA)
MUESTRAS_POR_CELDA = 4
ITERACIONES_AJUSTE = 25


@njit(cache=True)
def _trazar(brechas, factor, lon_min, lon_max, construible, costo_m, impacto_m, tam, mascara):
    """Dibuja las brechas en ``mascara`` y devuelve (costo, impacto).

    Las longitudes se multiplican por ``factor`` y se acotan a [lon_min, lon_max]. Se avanza
    por el segmento en pasos de un cuarto de celda: cada paso sobre terreno construible suma
    su tramo al costo; los tramos fuera del mapa, sobre agua o sobre poblados se omiten.
    Cuando el trazo cambia de fila y columna a la vez se marca la celda de la esquina, para
    que la brecha sea 4-conexa y el fuego no la cruce en diagonal.
    """
    filas, cols = mascara.shape
    paso = tam / MUESTRAS_POR_CELDA
    costo = 0.0
    impacto = 0.0
    for k in range(brechas.shape[0]):
        longitud = min(max(brechas[k, LONGITUD] * factor, lon_min), lon_max)
        angulo = np.radians(brechas[k, ANGULO])
        dx = np.cos(angulo)
        dy = np.sin(angulo)
        n = int(np.ceil(longitud / paso))
        ds = longitud / n
        f_prev = -1
        c_prev = -1
        prev_ok = False
        for i in range(n):
            s = (i + 0.5) * ds
            c = int(np.floor((brechas[k, X] + dx * s) / tam))
            f = int(np.floor((brechas[k, Y] + dy * s) / tam))
            ok = 0 <= f < filas and 0 <= c < cols and construible[f, c]
            if ok:
                costo += ds * costo_m[f, c]
                impacto += ds * impacto_m[f, c]
                mascara[f, c] = True
                if prev_ok and f != f_prev and c != c_prev:
                    if construible[f_prev, c]:
                        mascara[f_prev, c] = True
                    elif construible[f, c_prev]:
                        mascara[f, c_prev] = True
            f_prev = f
            c_prev = c
            prev_ok = ok
    return costo, impacto


@njit(cache=True)
def _factor_dentro_de_presupuesto(brechas, f_max, presupuesto, lon_min, lon_max, construible,
                                  costo_m, impacto_m, tam, mascara):
    """Mayor factor de escala en [0, f_max] cuyo costo no excede el presupuesto."""
    mascara[:, :] = False
    costo, _ = _trazar(brechas, f_max, lon_min, lon_max, construible, costo_m, impacto_m, tam,
                       mascara)
    if costo <= presupuesto:
        return f_max
    bajo = 0.0
    alto = f_max
    for _ in range(ITERACIONES_AJUSTE):
        medio = 0.5 * (bajo + alto)
        mascara[:, :] = False
        costo, _ = _trazar(brechas, medio, lon_min, lon_max, construible, costo_m, impacto_m,
                           tam, mascara)
        if costo <= presupuesto:
            bajo = medio
        else:
            alto = medio
    return bajo


@njit(parallel=True, cache=True)
def _ajustar_poblacion(poblacion, f_max, presupuesto, lon_min, lon_max, construible, costo_m,
                       impacto_m, tam):
    filas, cols = construible.shape
    for i in prange(poblacion.shape[0]):
        mascara = np.zeros((filas, cols), dtype=np.bool_)
        f = _factor_dentro_de_presupuesto(poblacion[i], f_max, presupuesto, lon_min, lon_max,
                                          construible, costo_m, impacto_m, tam, mascara)
        for k in range(poblacion.shape[1]):
            poblacion[i, k, LONGITUD] = min(max(poblacion[i, k, LONGITUD] * f, lon_min), lon_max)


@njit(parallel=True, cache=True)
def _trazar_poblacion(poblacion, lon_min, lon_max, construible, costo_m, impacto_m, tam,
                      mascaras, costos, impactos):
    for i in prange(poblacion.shape[0]):
        costos[i], impactos[i] = _trazar(poblacion[i], 1.0, lon_min, lon_max, construible,
                                         costo_m, impacto_m, tam, mascaras[i])


@dataclass(frozen=True)
class PlanesTrazados:
    mascaras: np.ndarray
    """Celdas desmontadas de cada plan: (planes, filas, columnas)."""
    costos: np.ndarray
    impactos: np.ndarray


class TrazadorBrechas:
    """Convierte cromosomas en brechas sobre un mapa y aplica la restricción de presupuesto."""

    def __init__(self, mapa: Mapa, config: ConfigBrechas) -> None:
        self.mapa = mapa
        self.config = config
        veg, den = mapa.vegetacion, mapa.densidad
        relieve = 1.0 + mapa.pendiente_grados / cat.PENDIENTE_REFERENCIA_GRADOS
        self.costo_por_metro = np.ascontiguousarray(
            cat.tabla_vegetacion("costo_desmonte_m")[veg]
            * cat.tabla_densidad("factor_costo")[den]
            * relieve
        )
        """Pesos por metro de brecha en cada celda."""
        self.impacto_por_metro = np.ascontiguousarray(
            cat.tabla_vegetacion("valor_ecologico")[veg]
            * cat.tabla_densidad("factor_ecologico")[den]
            * config.ancho_m
            / 10_000.0
        )
        """Hectáreas equivalentes de vegetación valiosa por metro de brecha."""
        self._construible = np.ascontiguousarray(mapa.construible)

    @property
    def n_genes(self) -> int:
        return self.config.k * GENES_POR_BRECHA

    def limites(self) -> tuple[np.ndarray, np.ndarray]:
        """Rango de cada gen del cromosoma."""
        c = self.config
        inferior = np.tile([0.0, 0.0, 0.0, c.longitud_min_m], c.k)
        superior = np.tile([self.mapa.ancho_m, self.mapa.alto_m, 360.0, c.longitud_max_m], c.k)
        return inferior, superior

    def brechas(self, poblacion: np.ndarray) -> np.ndarray:
        """Vista (planes, K, 4) de una población (planes, 4K) o de un solo cromosoma."""
        return np.atleast_2d(poblacion).reshape(-1, self.config.k, GENES_POR_BRECHA)

    def _ajustar(self, poblacion: np.ndarray, f_max: float) -> np.ndarray:
        c = self.config
        brechas = np.ascontiguousarray(self.brechas(poblacion), dtype=np.float64).copy()
        with CANDADO:
            _ajustar_poblacion(
                brechas, f_max, c.presupuesto, c.longitud_min_m, c.longitud_max_m,
                self._construible, self.costo_por_metro, self.impacto_por_metro,
                self.mapa.tam_celda_m,
            )  # fmt: skip
        return brechas.reshape(np.atleast_2d(poblacion).shape)

    def reparar(self, poblacion: np.ndarray) -> np.ndarray:
        """Acorta en proporción las brechas de los planes que exceden el presupuesto.

        Los planes que ya cumplen no cambian. Si un plan sigue excedido con todas sus brechas
        en la longitud mínima, queda como infactible.
        """
        return self._ajustar(poblacion, 1.0)

    def ajustar_al_presupuesto(self, poblacion: np.ndarray) -> np.ndarray:
        """Escala las longitudes, hacia arriba o abajo, para gastar todo el presupuesto."""
        c = self.config
        return self._ajustar(poblacion, c.longitud_max_m / c.longitud_min_m)

    def trazar(self, poblacion: np.ndarray) -> PlanesTrazados:
        c = self.config
        brechas = np.ascontiguousarray(self.brechas(poblacion), dtype=np.float64)
        n = brechas.shape[0]
        mascaras = np.zeros((n, *self.mapa.forma), dtype=np.bool_)
        costos = np.empty(n)
        impactos = np.empty(n)
        with CANDADO:
            _trazar_poblacion(
                brechas, c.longitud_min_m, c.longitud_max_m, self._construible,
                self.costo_por_metro, self.impacto_por_metro, self.mapa.tam_celda_m,
                mascaras, costos, impactos,
            )  # fmt: skip
        return PlanesTrazados(mascaras, costos, impactos)

    def poblacion_aleatoria(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Planes al azar dentro de los rangos, ya reparados."""
        inferior, superior = self.limites()
        return self.reparar(rng.uniform(inferior, superior, size=(n, self.n_genes)))
