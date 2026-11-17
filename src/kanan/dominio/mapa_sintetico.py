"""Generador de un mapa sintético con los rasgos de La Sepultura.

Una sierra que sube hacia el noreste, vegetación ordenada por altitud y humedad, un río que
baja de la sierra, poblados con cultivos en la parte baja, caminos entre ellos y la parte
alta como zona núcleo.
"""

from __future__ import annotations

import numpy as np

from kanan.config import ConfigMapa
from kanan.dominio import catalogos as cat
from kanan.dominio.mapa import Mapa

N_POBLADOS = 3
RADIO_POBLADO = 1
RADIO_CULTIVO = 4


def _ruido_suave(rng: np.random.Generator, forma: tuple[int, int], escala: int) -> np.ndarray:
    """Ruido en [0, 1] con manchas de unas ``escala`` celdas (interpolación bilineal)."""
    filas, cols = forma
    nf, nc = filas // escala + 2, cols // escala + 2
    base = rng.random((nf, nc))
    f = np.arange(filas) / escala
    c = np.arange(cols) / escala
    f0, c0 = f.astype(int), c.astype(int)
    tf, tc = (f - f0)[:, None], (c - c0)[None, :]
    a = base[f0][:, c0]
    b = base[f0][:, c0 + 1]
    d = base[f0 + 1][:, c0]
    e = base[f0 + 1][:, c0 + 1]
    return a * (1 - tf) * (1 - tc) + b * (1 - tf) * tc + d * tf * (1 - tc) + e * tf * tc


def _distancia(mascara: np.ndarray) -> np.ndarray:
    """Distancia en celdas (Chebyshev) a la celda marcada más cercana."""
    dist = np.where(mascara, 0.0, np.inf)
    for _ in range(max(mascara.shape)):
        relleno = np.pad(dist, 1, constant_values=np.inf)
        vecinos = np.min(
            [
                relleno[1 + df : 1 + df + dist.shape[0], 1 + dc : 1 + dc + dist.shape[1]]
                for df in (-1, 0, 1)
                for dc in (-1, 0, 1)
            ],
            axis=0,
        )
        nueva = np.minimum(dist, vecinos + 1)
        if np.array_equal(nueva, dist):
            break
        dist = nueva
    return dist


def _linea(f0: int, c0: int, f1: int, c1: int) -> list[tuple[int, int]]:
    n = max(abs(f1 - f0), abs(c1 - c0)) + 1
    filas = np.rint(np.linspace(f0, f1, n)).astype(int)
    cols = np.rint(np.linspace(c0, c1, n)).astype(int)
    return list(zip(filas.tolist(), cols.tolist(), strict=True))


def _trazar_rio(elevacion: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Río 4-conexo que baja desde la sierra hasta salir del mapa."""
    filas, cols = elevacion.shape
    rio = np.zeros(elevacion.shape, dtype=bool)
    f, c = int(filas * 0.12), int(cols * rng.uniform(0.45, 0.6))
    for _ in range(4 * (filas + cols)):
        rio[f, c] = True
        if f == filas - 1 or c == 0:
            break
        candidatos = [(f + 1, c), (f, c - 1), (f, c + 1)]
        candidatos = [
            (nf, nc)
            for nf, nc in candidatos
            if 0 <= nf < filas and 0 <= nc < cols and not rio[nf, nc]
        ]
        if not candidatos:
            break
        # Baja por la pendiente con algo de azar para que serpentee.
        costos = [elevacion[p] + rng.normal(0, 25) for p in candidatos]
        f, c = candidatos[int(np.argmin(costos))]
    return rio


def _ubicar_poblados(
    elevacion: np.ndarray, rio: np.ndarray, rng: np.random.Generator
) -> list[tuple[int, int]]:
    """Centros en la parte baja, lejos del borde, del río y entre sí."""
    filas, cols = elevacion.shape
    margen = RADIO_CULTIVO + 2
    limite_bajo = np.quantile(elevacion, 0.45)
    lejos_rio = _distancia(rio) > 3
    separacion = min(filas, cols) / 4
    centros: list[tuple[int, int]] = []
    for _ in range(5000):
        if len(centros) == N_POBLADOS:
            break
        f = int(rng.integers(margen, filas - margen))
        c = int(rng.integers(margen, cols - margen))
        if elevacion[f, c] > limite_bajo or not lejos_rio[f, c]:
            continue
        if all(np.hypot(f - pf, c - pc) >= separacion for pf, pc in centros):
            centros.append((f, c))
    if len(centros) < N_POBLADOS:
        raise RuntimeError("no fue posible ubicar los poblados; pruebe otra semilla o tamaño")
    return centros


def generar_mapa_sintetico(config: ConfigMapa) -> Mapa:
    rng = np.random.default_rng(config.semilla)
    forma = (config.filas, config.columnas)
    filas, cols = forma
    if min(forma) < 40:
        raise ValueError("el mapa sintético requiere al menos 40 x 40 celdas")

    # Relieve: sierra hacia el noreste más lomeríos.
    ff, cc = np.meshgrid(np.linspace(0, 1, filas), np.linspace(0, 1, cols), indexing="ij")
    rampa = 0.55 * (1 - ff) + 0.45 * cc
    relieve = 0.7 * rampa + 0.2 * _ruido_suave(rng, forma, 16) + 0.1 * _ruido_suave(rng, forma, 6)
    relieve = (relieve - relieve.min()) / (relieve.max() - relieve.min())
    # Desnivel proporcional al tamaño del área para mantener pendientes realistas.
    desnivel = 0.16 * min(filas, cols) * config.tam_celda_m
    elevacion = (300.0 + desnivel * relieve).astype(np.float32)

    # Vegetación por altitud y humedad.
    humedad = _ruido_suave(rng, forma, 10)
    vegetacion = np.full(forma, cat.SELVA_BAJA, dtype=np.int8)
    vegetacion[(relieve < 0.35) & (humedad < 0.45)] = cat.PASTIZAL
    vegetacion[relieve >= 0.5] = cat.PINO_ENCINO
    vegetacion[(relieve >= 0.5) & (relieve < 0.62) & (humedad < 0.35)] = cat.SELVA_BAJA
    vegetacion[(relieve >= 0.78) & (humedad > 0.4)] = cat.MESOFILO

    ruido_den = _ruido_suave(rng, forma, 7)
    densidad = np.full(forma, cat.NORMAL, dtype=np.int8)
    densidad[ruido_den < 0.35] = cat.RALA
    densidad[ruido_den > 0.62] = cat.DENSA

    zona = np.zeros(forma, dtype=np.int8)
    zona[relieve >= 0.7] = cat.Z_NUCLEO

    rio = _trazar_rio(elevacion, rng)
    centros = _ubicar_poblados(elevacion, rio, rng)

    # Cultivos alrededor de cada poblado, con borde irregular.
    borde = _ruido_suave(rng, forma, 4)
    for f, c in centros:
        dist = np.hypot(np.arange(filas)[:, None] - f, np.arange(cols)[None, :] - c)
        parcela = dist <= RADIO_CULTIVO * (0.6 + 0.8 * borde)
        vegetacion[parcela] = cat.AGRICULTURA
        densidad[parcela] = cat.RALA
        zona[parcela] = cat.Z_CULTIVO

    # Caminos: unen los poblados en cadena y salen por el borde sur.
    caminos = np.zeros(forma, dtype=bool)
    orden = sorted(centros, key=lambda p: p[1])
    tramos = list(zip(orden[:-1], orden[1:], strict=True))
    tramos.append((orden[0], (filas - 1, orden[0][1])))
    celdas_camino: list[tuple[int, int]] = []
    for (f0, c0), (f1, c1) in tramos:
        celdas_camino += _linea(f0, c0, f1, c1)
    for f, c in celdas_camino:
        caminos[f, c] = True

    # Infraestructura: instalaciones a mitad de cada tramo de camino entre poblados.
    for (f0, c0), (f1, c1) in tramos[:-1]:
        zona[(f0 + f1) // 2, (c0 + c1) // 2] = cat.Z_INFRAESTRUCTURA

    for f, c in centros:
        bloque = (
            slice(f - RADIO_POBLADO, f + RADIO_POBLADO + 1),
            slice(c - RADIO_POBLADO, c + RADIO_POBLADO + 1),
        )
        vegetacion[bloque] = cat.POBLADO
        densidad[bloque] = cat.RALA
        zona[bloque] = cat.Z_POBLADO

    vegetacion[rio] = cat.AGUA
    zona[rio] = cat.SIN_ZONA
    caminos[rio] = False

    # Ignición: casi todos los incendios son de origen humano, cerca de caminos y parcelas.
    combustible = cat.tabla_vegetacion("combustible")[vegetacion]
    actividad = caminos | (zona == cat.Z_CULTIVO)
    riesgo = 0.15 + np.exp(-_distancia(actividad) / 3.0)
    riesgo[~combustible] = 0.0
    riesgo[vegetacion == cat.POBLADO] = 0.0
    prob_ignicion = riesgo / riesgo.sum()

    return Mapa(
        vegetacion=vegetacion,
        densidad=densidad,
        elevacion=elevacion,
        zona_valor=zona,
        caminos=caminos,
        prob_ignicion=prob_ignicion,
        tam_celda_m=config.tam_celda_m,
        poblados=tuple((f, c, RADIO_POBLADO) for f, c in centros),
    )


def construir_mapa(config: ConfigMapa) -> Mapa:
    """Punto único de construcción; aquí se agregará el mapa real de INEGI."""
    if config.tipo == "sintetico":
        return generar_mapa_sintetico(config)
    raise ValueError(f"tipo de mapa no soportado: {config.tipo}")
