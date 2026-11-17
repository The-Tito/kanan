"""Autómata celular de propagación del fuego (Alexandridis et al., 2008).

En cada paso, una celda en llamas intenta encender a cada una de sus 8 vecinas con
probabilidad ``p_burn = p_h (1 + p_veg)(1 + p_den) p_w p_s`` y después queda quemada.

El azar de cada intento no sale de una secuencia sino de una función de la semilla del
escenario, la celda de origen y la dirección. Así dos planes distintos simulados en el mismo
escenario comparten exactamente la misma "suerte" y solo difieren por sus brechas (ver ADR
004).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit, prange

from kanan.config import ConfigFuego
from kanan.dominio import catalogos as cat
from kanan.dominio.mapa import Mapa
from kanan.simulacion.escenarios import Escenarios

# Vecindad de Moore en orden horario desde el norte: N, NE, E, SE, S, SO, O, NO.
D_FILA = np.array([-1, -1, 0, 1, 1, 1, 0, -1], dtype=np.int64)
D_COL = np.array([0, 1, 1, 1, 0, -1, -1, -1], dtype=np.int64)
AZIMUT_VECINO = np.arange(8) * 45.0

_ORO = np.uint64(0x9E3779B97F4A7C15)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
_S30, _S27, _S31, _S11 = np.uint64(30), np.uint64(27), np.uint64(31), np.uint64(11)
_A_UNITARIO = 1.0 / 9007199254740992.0  # 2**-53


@njit(cache=True)
def _uniforme(semilla, indice):
    """Número en [0, 1) determinado por (semilla, índice) con el mezclador splitmix64."""
    x = semilla + indice * _ORO
    x ^= x >> _S30
    x *= _M1
    x ^= x >> _S27
    x *= _M2
    x ^= x >> _S31
    return (x >> _S11) * _A_UNITARIO


@njit(cache=True)
def _propagar(p_celda, p_pendiente, combustible, fila0, col0, p_viento, semilla, duracion, t_ign,
              frente):
    """Simula un incendio. Llena ``t_ign`` con el paso de ignición (-1 si no ardió).

    Solo recorre el frente activo: las celdas que se encendieron en el paso anterior.
    Devuelve el número de celdas quemadas.
    """
    filas, cols = t_ign.shape
    t_ign[:, :] = -1
    # La ignición ocurre aunque haya una brecha encima: tapar el punto de inicio no cuenta.
    t_ign[fila0, col0] = 0
    frente[0, 0] = fila0 * cols + col0
    n = 1
    quemadas = 1
    actual = 0
    t = 0
    while n > 0 and t < duracion:
        t += 1
        m = 0
        for i in range(n):
            origen = frente[actual, i]
            f = origen // cols
            c = origen % cols
            for d in range(8):
                nf = f + D_FILA[d]
                nc = c + D_COL[d]
                if nf < 0 or nf >= filas or nc < 0 or nc >= cols:
                    continue
                if t_ign[nf, nc] != -1 or not combustible[nf, nc]:
                    continue
                p = p_celda[nf, nc] * p_viento[d] * p_pendiente[d, f, c]
                if p >= 1.0 or _uniforme(semilla, np.uint64(origen * 8 + d)) < p:
                    t_ign[nf, nc] = t
                    frente[1 - actual, m] = nf * cols + nc
                    m += 1
        actual = 1 - actual
        n = m
        quemadas += m
    return quemadas


@njit(parallel=True, cache=True)
def _simular_lote(p_celda, p_pendiente, combustible_base, brechas, filas0, cols0, p_vientos,
                  semillas, duracion, valor_celda, area, valor):
    """Simula cada plan (máscara de brechas) en cada escenario."""
    n_planes = brechas.shape[0]
    n_esc = filas0.shape[0]
    filas, cols = combustible_base.shape
    for k in prange(n_planes * n_esc):
        i = k // n_esc
        s = k % n_esc
        combustible = combustible_base & ~brechas[i]
        t_ign = np.empty((filas, cols), dtype=np.int32)
        frente = np.empty((2, filas * cols), dtype=np.int64)
        area[i, s] = _propagar(p_celda, p_pendiente, combustible, filas0[s], cols0[s],
                               p_vientos[s], semillas[s], duracion, t_ign, frente)
        total = 0.0
        for f in range(filas):
            for c in range(cols):
                if t_ign[f, c] >= 0:
                    total += valor_celda[f, c]
        valor[i, s] = total


@njit(parallel=True, cache=True)
def _contar_quemas(p_celda, p_pendiente, combustible, filas0, cols0, p_vientos, semillas,
                   duracion, t_todos):
    """Guarda el paso de ignición de cada celda en cada escenario."""
    filas, cols = combustible.shape
    for s in prange(filas0.shape[0]):
        frente = np.empty((2, filas * cols), dtype=np.int64)
        _propagar(p_celda, p_pendiente, combustible, filas0[s], cols0[s], p_vientos[s],
                  semillas[s], duracion, t_todos[s], frente)


def factor_pendiente(elevacion: np.ndarray, tam_celda_m: float, a: float) -> np.ndarray:
    """``p_s = exp(a·θ)`` por dirección y celda de origen; θ en grados, positivo cuesta arriba."""
    filas, cols = elevacion.shape
    elev = elevacion.astype(np.float64)
    relleno = np.pad(elev, 1, mode="edge")
    factores = np.empty((8, filas, cols))
    for d in range(8):
        vecina = relleno[1 + D_FILA[d] : 1 + D_FILA[d] + filas, 1 + D_COL[d] : 1 + D_COL[d] + cols]
        distancia = tam_celda_m * (np.sqrt(2.0) if d % 2 else 1.0)
        factores[d] = np.exp(a * np.degrees(np.arctan((vecina - elev) / distancia)))
    return factores


def factor_viento(velocidad: np.ndarray, azimut: np.ndarray, c1: float, c2: float) -> np.ndarray:
    """``p_w = exp(V (c1 + c2 (cos θ - 1)))`` por escenario y dirección de avance."""
    theta = np.radians(AZIMUT_VECINO[None, :] - np.asarray(azimut, dtype=float)[:, None])
    v = np.asarray(velocidad, dtype=float)[:, None]
    return np.exp(v * (c1 + c2 * (np.cos(theta) - 1.0)))


@dataclass(frozen=True)
class Incendio:
    """Resultado de una simulación individual."""

    t_ignicion: np.ndarray
    """Paso en que ardió cada celda; -1 si no ardió."""

    @property
    def quemado(self) -> np.ndarray:
        return self.t_ignicion >= 0

    @property
    def celdas_quemadas(self) -> int:
        return int(self.quemado.sum())

    @property
    def duracion(self) -> int:
        return int(self.t_ignicion.max())


class SimuladorFuego:
    """Precalcula lo que depende solo del mapa y simula planes sobre escenarios."""

    def __init__(self, mapa: Mapa, config: ConfigFuego) -> None:
        self.mapa = mapa
        self.config = config
        p_veg = cat.tabla_vegetacion("p_veg")[mapa.vegetacion]
        p_den = cat.tabla_densidad("p_den")[mapa.densidad]
        self._p_celda = np.ascontiguousarray(config.p_h * (1.0 + p_veg) * (1.0 + p_den))
        self._p_pendiente = factor_pendiente(mapa.elevacion, mapa.tam_celda_m, config.a_pendiente)
        self._combustible = np.ascontiguousarray(mapa.combustible)

    def _vientos(self, escenarios: Escenarios) -> np.ndarray:
        return factor_viento(
            escenarios.viento_vel, escenarios.viento_dir, self.config.c1, self.config.c2
        )

    def _combustible_con(self, brechas: np.ndarray | None) -> np.ndarray:
        if brechas is None:
            return self._combustible
        return self._combustible & ~brechas

    def simular_lote(
        self, brechas: np.ndarray, escenarios: Escenarios, valor_celda: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Celdas quemadas y valor afectado de cada plan en cada escenario.

        ``brechas`` tiene forma (planes, filas, columnas). Devuelve dos matrices de forma
        (planes, escenarios).
        """
        n = brechas.shape[0]
        area = np.empty((n, len(escenarios)))
        valor = np.empty((n, len(escenarios)))
        _simular_lote(
            self._p_celda, self._p_pendiente, self._combustible, brechas,
            escenarios.filas, escenarios.columnas, self._vientos(escenarios), escenarios.semillas,
            self.config.duracion_max, np.ascontiguousarray(valor_celda, dtype=np.float64),
            area, valor,
        )  # fmt: skip
        return area, valor

    def tiempos_ignicion(self, brechas: np.ndarray | None, escenarios: Escenarios) -> np.ndarray:
        """Paso de ignición por celda para cada escenario: (escenarios, filas, columnas)."""
        t_todos = np.empty((len(escenarios), *self.mapa.forma), dtype=np.int32)
        _contar_quemas(
            self._p_celda, self._p_pendiente, self._combustible_con(brechas),
            escenarios.filas, escenarios.columnas, self._vientos(escenarios), escenarios.semillas,
            self.config.duracion_max, t_todos,
        )  # fmt: skip
        return t_todos

    def simular(self, brechas: np.ndarray | None, escenarios: Escenarios, i: int = 0) -> Incendio:
        """Un incendio completo: la interfaz ``simular(plan, escenario)`` del brief."""
        return Incendio(self.tiempos_ignicion(brechas, escenarios.uno(i))[0])

    def probabilidad_quema(self, brechas: np.ndarray | None, escenarios: Escenarios) -> np.ndarray:
        """Fracción de escenarios en que arde cada celda."""
        return (self.tiempos_ignicion(brechas, escenarios) >= 0).mean(axis=0)
