"""Tablas de resultados: filas listas para CSV y para el reporte."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from kanan.optimizacion.aptitud import OBJETIVOS
from kanan.validacion.comparacion import ResultadoMetodo

Fila = dict[str, object]


def escribir_csv(filas: list[Fila], ruta: Path) -> None:
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def filas_brechas(nombre: str, brechas: np.ndarray) -> list[Fila]:
    """Los genes de cada brecha de un plan."""
    return [
        {
            "plan": nombre,
            "brecha": k + 1,
            "x_inicio_m": round(float(b[0]), 1),
            "y_inicio_m": round(float(b[1]), 1),
            "angulo_grados": round(float(b[2]), 1),
            "longitud_m": round(float(b[3]), 1),
        }
        for k, b in enumerate(brechas)
    ]


def filas_frente(planes: np.ndarray, objetivos: np.ndarray) -> list[Fila]:
    """Todo el frente de Pareto: objetivos y cromosoma de cada plan."""
    filas = []
    for i, (plan, fila_obj) in enumerate(zip(planes, objetivos, strict=True)):
        fila: Fila = {"plan": i}
        fila.update({o: round(float(v), 4) for o, v in zip(OBJETIVOS, fila_obj, strict=True)})
        fila.update({f"gen_{g}": round(float(v), 2) for g, v in enumerate(plan)})
        filas.append(fila)
    return filas


def filas_comparacion(resultados: list[ResultadoMetodo], base: ResultadoMetodo) -> list[Fila]:
    return [
        {
            "metodo": r.nombre,
            "planes": r.n_planes,
            "area_media_ha": round(r.area_media, 1),
            "area_desviacion_ha": round(r.area_desviacion, 1),
            "area_mediana_ha": round(r.area_mediana, 1),
            "area_p90_ha": round(r.area_p90, 1),
            "reduccion_vs_sin_brechas": round(r.reduccion_frente_a(base), 4),
            "valor_afectado": round(r.valor_medio, 1),
            "costo": round(r.costo_medio, 0),
            "impacto_ecologico": round(r.impacto_medio, 2),
        }
        for r in resultados
    ]
