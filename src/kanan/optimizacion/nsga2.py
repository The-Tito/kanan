"""NSGA-II (Deb et al., 2002) para minimización con genes reales.

Este módulo no sabe nada de incendios: recibe una función de evaluación, los límites de los
genes y, opcionalmente, una función de reparación.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from kanan.config import ConfigAG

Evaluar = Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]]
"""Población (n, genes) → objetivos (n, m) y violación de restricciones (n,), 0 si cumple."""


def matriz_dominancia(objetivos: np.ndarray, violacion: np.ndarray | None = None) -> np.ndarray:
    """``d[i, j]`` es verdadero si ``i`` domina a ``j`` (dominancia restringida de Deb)."""
    menor_o_igual = (objetivos[:, None, :] <= objetivos[None, :, :]).all(axis=2)
    menor = (objetivos[:, None, :] < objetivos[None, :, :]).any(axis=2)
    domina = menor_o_igual & menor
    if violacion is None:
        return domina
    factible = violacion <= 0
    ambos = factible[:, None] & factible[None, :]
    solo_i = factible[:, None] & ~factible[None, :]
    ninguno = ~factible[:, None] & ~factible[None, :]
    menos_exceso = violacion[:, None] < violacion[None, :]
    return (ambos & domina) | solo_i | (ninguno & menos_exceso)


def ordenamiento_no_dominado(
    objetivos: np.ndarray, violacion: np.ndarray | None = None
) -> np.ndarray:
    """Rango de Pareto de cada individuo; 0 es el frente no dominado."""
    domina = matriz_dominancia(objetivos, violacion)
    dominadores = domina.sum(axis=0)
    rangos = np.full(len(objetivos), -1)
    rango = 0
    actual = np.flatnonzero(dominadores == 0)
    while actual.size:
        rangos[actual] = rango
        dominadores[actual] = -1
        dominadores -= domina[actual].sum(axis=0)
        actual = np.flatnonzero(dominadores == 0)
        rango += 1
    return rangos


def distancia_apinamiento(objetivos: np.ndarray, rangos: np.ndarray) -> np.ndarray:
    """Distancia de apiñamiento dentro de cada frente; los extremos reciben infinito."""
    distancia = np.zeros(len(objetivos))
    for rango in np.unique(rangos):
        indices = np.flatnonzero(rangos == rango)
        if indices.size <= 2:
            distancia[indices] = np.inf
            continue
        frente = objetivos[indices]
        for m in range(objetivos.shape[1]):
            orden = np.argsort(frente[:, m], kind="stable")
            valores = frente[orden, m]
            amplitud = valores[-1] - valores[0]
            distancia[indices[orden[[0, -1]]]] = np.inf
            if amplitud > 0:
                distancia[indices[orden[1:-1]]] += (valores[2:] - valores[:-2]) / amplitud
    return distancia


def torneo_binario(
    rng: np.random.Generator, rangos: np.ndarray, apinamiento: np.ndarray, n: int
) -> np.ndarray:
    """Gana el de menor rango; si empatan, el de mayor distancia de apiñamiento."""
    a = rng.integers(0, len(rangos), size=n)
    b = rng.integers(0, len(rangos), size=n)
    empate = rangos[a] == rangos[b]
    gana_a = (rangos[a] < rangos[b]) | (empate & (apinamiento[a] >= apinamiento[b]))
    return np.where(gana_a, a, b)


def intercambio_de_bloques(
    rng: np.random.Generator, a: np.ndarray, b: np.ndarray, tam_bloque: int, p: float
) -> tuple[np.ndarray, np.ndarray]:
    """Cruza uniforme por bloques: cada bloque completo se intercambia con probabilidad ``p``."""
    n, genes = a.shape
    cambiar = np.repeat(rng.random((n, genes // tam_bloque)) < p, tam_bloque, axis=1)
    return np.where(cambiar, b, a), np.where(cambiar, a, b)


def cruza_sbx(
    rng: np.random.Generator, a: np.ndarray, b: np.ndarray, eta: float
) -> tuple[np.ndarray, np.ndarray]:
    """Cruza binaria simulada; cada gen se cruza con probabilidad 0.5."""
    u = rng.random(a.shape)
    exponente = 1 / (eta + 1)
    beta = np.where(u <= 0.5, (2 * u) ** exponente, (1 / (2 * (1 - u))) ** exponente)
    beta = np.where(rng.random(a.shape) < 0.5, beta, 1.0)
    hijo_a = 0.5 * ((1 + beta) * a + (1 - beta) * b)
    hijo_b = 0.5 * ((1 - beta) * a + (1 + beta) * b)
    return hijo_a, hijo_b


def mutacion_polinomial(
    rng: np.random.Generator, x: np.ndarray, amplitud: np.ndarray, p: float, eta: float
) -> np.ndarray:
    """Desplaza cada gen con probabilidad ``p`` una fracción de su rango."""
    u = rng.random(x.shape)
    exponente = 1 / (eta + 1)
    delta = np.where(u < 0.5, (2 * u) ** exponente - 1, 1 - (2 * (1 - u)) ** exponente)
    return np.where(rng.random(x.shape) < p, x + delta * amplitud, x)


@dataclass(frozen=True)
class Historial:
    """Objetivos, violaciones y rangos de la población en cada generación (0 = inicial)."""

    objetivos: np.ndarray
    violacion: np.ndarray
    rangos: np.ndarray

    def _factibles(self) -> np.ndarray:
        return np.where((self.violacion <= 0)[:, :, None], self.objetivos, np.nan)

    def mejor(self) -> np.ndarray:
        """Mínimo de cada objetivo por generación: (generaciones, objetivos)."""
        return np.nanmin(self._factibles(), axis=1)

    def promedio(self) -> np.ndarray:
        return np.nanmean(self._factibles(), axis=1)

    def frente(self, generacion: int) -> np.ndarray:
        """Objetivos del frente no dominado factible de una generación."""
        primero = (self.rangos[generacion] == 0) & (self.violacion[generacion] <= 0)
        return self.objetivos[generacion][primero]


@dataclass(frozen=True)
class ResultadoAG:
    poblacion: np.ndarray
    objetivos: np.ndarray
    violacion: np.ndarray
    rangos: np.ndarray
    historial: Historial
    evaluaciones: int

    def frente(self) -> tuple[np.ndarray, np.ndarray]:
        """Individuos y objetivos del frente no dominado factible, sin duplicados."""
        primero = (self.rangos == 0) & (self.violacion <= 0)
        _, unicos = np.unique(self.objetivos[primero].round(9), axis=0, return_index=True)
        unicos.sort()
        return self.poblacion[primero][unicos], self.objetivos[primero][unicos]


class NSGA2:
    def __init__(
        self,
        config: ConfigAG,
        inferior: np.ndarray,
        superior: np.ndarray,
        *,
        tam_bloque: int = 1,
        periodicos: np.ndarray | None = None,
        reparar: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> None:
        """``periodicos`` marca los genes circulares (ángulos), que dan la vuelta al salirse."""
        self.config = config
        self.inferior = np.asarray(inferior, dtype=float)
        self.superior = np.asarray(superior, dtype=float)
        self.amplitud = self.superior - self.inferior
        self.n_genes = len(self.inferior)
        self.tam_bloque = tam_bloque
        self.periodicos = np.zeros(self.n_genes, dtype=bool) if periodicos is None else periodicos
        self.reparar = reparar or (lambda poblacion: poblacion)
        self.p_mutacion = config.p_mutacion or 1.0 / self.n_genes
        self.rng = np.random.default_rng(config.semilla)

    def _a_rango(self, x: np.ndarray) -> np.ndarray:
        circular = self.inferior + np.mod(x - self.inferior, self.amplitud)
        return np.where(self.periodicos, circular, np.clip(x, self.inferior, self.superior))

    def poblacion_inicial(self) -> np.ndarray:
        forma = (self.config.poblacion, self.n_genes)
        return self.reparar(self.rng.uniform(self.inferior, self.superior, size=forma))

    def _descendencia(
        self, poblacion: np.ndarray, rangos: np.ndarray, apinamiento: np.ndarray
    ) -> np.ndarray:
        c, rng = self.config, self.rng
        n = len(poblacion)
        padres = poblacion[torneo_binario(rng, rangos, apinamiento, n)]
        a, b = padres[: n // 2], padres[n // 2 :]
        hijo_a, hijo_b = intercambio_de_bloques(rng, a, b, self.tam_bloque, c.p_intercambio_brecha)
        hijo_a, hijo_b = cruza_sbx(rng, hijo_a, hijo_b, c.eta_cruza)
        se_cruza = rng.random((n // 2, 1)) < c.p_cruza
        hijos = np.vstack([np.where(se_cruza, hijo_a, a), np.where(se_cruza, hijo_b, b)])
        hijos = mutacion_polinomial(rng, hijos, self.amplitud, self.p_mutacion, c.eta_mutacion)
        return self.reparar(self._a_rango(hijos))

    def ejecutar(
        self,
        evaluar: Evaluar,
        al_avanzar: Callable[[int, int], None] | None = None,
    ) -> ResultadoAG:
        c = self.config
        n = c.poblacion
        poblacion = self.poblacion_inicial()
        objetivos, violacion = evaluar(poblacion)
        rangos = ordenamiento_no_dominado(objetivos, violacion)
        apin = distancia_apinamiento(objetivos, rangos)
        hist_obj, hist_viol, hist_rangos = [objetivos], [violacion], [rangos]

        for generacion in range(1, c.generaciones + 1):
            hijos = self._descendencia(poblacion, rangos, apin)
            obj_hijos, viol_hijos = evaluar(hijos)

            # Elitismo: padres e hijos compiten juntos y sobreviven los mejores frentes.
            todos = np.vstack([poblacion, hijos])
            obj_todos = np.vstack([objetivos, obj_hijos])
            viol_todos = np.concatenate([violacion, viol_hijos])
            rangos_todos = ordenamiento_no_dominado(obj_todos, viol_todos)
            apin_todos = distancia_apinamiento(obj_todos, rangos_todos)
            sobreviven = np.lexsort((-apin_todos, rangos_todos))[:n]

            poblacion = todos[sobreviven]
            objetivos, violacion = obj_todos[sobreviven], viol_todos[sobreviven]
            rangos = ordenamiento_no_dominado(objetivos, violacion)
            apin = distancia_apinamiento(objetivos, rangos)
            hist_obj.append(objetivos)
            hist_viol.append(violacion)
            hist_rangos.append(rangos)
            if al_avanzar:
                al_avanzar(generacion, c.generaciones)

        historial = Historial(np.array(hist_obj), np.array(hist_viol), np.array(hist_rangos))
        return ResultadoAG(
            poblacion, objetivos, violacion, rangos, historial, n * (c.generaciones + 1)
        )
