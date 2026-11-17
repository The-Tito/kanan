"""Datos reales de una corrida de Kanan para ilustrar el video.

Se ejecuta el mismo sistema que usa ``kanan ejecutar`` con la configuración por omisión, y
además se guarda el mejor plan de cada generación para poder animar la evolución.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from kanan.aplicacion.corrida import Sistema, construir_sistema, validar
from kanan.config import Config
from kanan.dominio.plan import GENES_POR_BRECHA
from kanan.optimizacion.aptitud import AREA
from kanan.optimizacion.nsga2 import NSGA2
from kanan.optimizacion.seleccion import elegir_planes


@dataclass(frozen=True)
class Corrida:
    objetivos_por_generacion: np.ndarray
    """(generaciones + 1, población, 4)."""
    mejor_plan_por_generacion: np.ndarray
    """Cromosoma de menor área quemada en cada generación."""
    poblacion_inicial: np.ndarray
    frente_planes: np.ndarray
    frente_objetivos: np.ndarray
    elegidos: dict[str, int]
    comparacion: list[tuple[str, float, float, bool]]
    """(método, área media en prueba, costo, es de Kanan)."""


def _correr(sistema: Sistema) -> Corrida:
    config = sistema.config
    genes_por_objetivo: dict[bytes, np.ndarray] = {}
    aptitud = sistema.evaluador.aptitud(sistema.entrenamiento)
    primera: list[np.ndarray] = []

    def evaluar(poblacion: np.ndarray):
        objetivos, violacion = aptitud(poblacion)
        if not primera:
            primera.append(poblacion.copy())
        for plan, fila in zip(poblacion, objetivos, strict=True):
            genes_por_objetivo[fila.tobytes()] = plan.copy()
        return objetivos, violacion

    inferior, superior = sistema.trazador.limites()
    nsga = NSGA2(config.ag, inferior, superior, tam_bloque=GENES_POR_BRECHA,
                 periodicos=np.tile([False, False, True, False], config.brechas.k),
                 reparar=sistema.trazador.reparar)  # fmt: skip
    ag = nsga.ejecutar(evaluar)
    historia = ag.historial.objetivos
    mejores = np.array(
        [genes_por_objetivo[gen[np.argmin(gen[:, AREA])].tobytes()] for gen in historia]
    )
    planes, objetivos = ag.frente()
    elegidos = elegir_planes(objetivos)
    comparacion = [
        (r.nombre, r.area_media, r.costo_medio, r.es_kanan)
        for r in validar(sistema, ag, planes, objetivos, elegidos)
    ]
    return Corrida(historia, mejores, primera[0], planes, objetivos, elegidos, comparacion)


def cargar(cache: Path) -> tuple[Sistema, Corrida]:
    """Construye el sistema y recupera la corrida del caché, o la ejecuta (cerca de un minuto)."""
    sistema = construir_sistema(Config())
    if cache.exists():
        return sistema, pickle.loads(cache.read_bytes())
    print("Ejecutando Kanan para obtener los datos del video (cerca de un minuto)...")
    corrida = _correr(sistema)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps(corrida))
    return sistema, corrida
