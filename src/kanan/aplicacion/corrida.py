"""Caso de uso principal: optimizar, validar y generar todas las salidas."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from kanan.config import Config
from kanan.dominio import catalogos as cat
from kanan.dominio.mapa import Mapa
from kanan.dominio.mapa_sintetico import construir_mapa
from kanan.dominio.plan import GENES_POR_BRECHA, TrazadorBrechas
from kanan.optimizacion.aptitud import AREA, OBJETIVOS, Evaluador
from kanan.optimizacion.hipervolumen import hipervolumen_por_generacion
from kanan.optimizacion.nsga2 import NSGA2, ResultadoAG
from kanan.optimizacion.seleccion import (
    EQUILIBRADO,
    MENOR_AREA,
    MENOR_COSTO,
    NOMBRES,
    elegir_planes,
)
from kanan.salidas import estilo, graficas, mapas, tablas
from kanan.salidas.reporte import DatosReporte, PlanReporte, generar_reporte
from kanan.simulacion.automata import SimuladorFuego
from kanan.simulacion.escenarios import Escenarios, generar_escenarios
from kanan.validacion import referencias
from kanan.validacion.comparacion import ResultadoMetodo, comparar

Avisar = Callable[[str], None]

SIN_BRECHAS = "Sin brechas"
AL_AZAR = "Brechas al azar"
POBLADOS = "Alrededor de poblados"
BUSQUEDA = "Búsqueda aleatoria"

DESCRIPCIONES = {
    MENOR_AREA: "El plan del frente que menos hectáreas deja arder en promedio.",
    MENOR_COSTO: "El más barato y de menor desmonte entre los planes que logran al menos la "
    "cuarta parte de la mejor reducción de área.",
    EQUILIBRADO: "El más cercano al punto ideal con los cuatro objetivos normalizados.",
}


@dataclass(frozen=True)
class Sistema:
    """Los objetos de una corrida, construidos una sola vez a partir de la configuración."""

    config: Config
    mapa: Mapa
    trazador: TrazadorBrechas
    simulador: SimuladorFuego
    evaluador: Evaluador
    entrenamiento: Escenarios
    prueba: Escenarios


@dataclass(frozen=True)
class ResultadoCorrida:
    sistema: Sistema
    ag: ResultadoAG
    frente_planes: np.ndarray
    frente_objetivos: np.ndarray
    elegidos: dict[str, int]
    """Índice en el frente de cada uno de los tres planes."""
    comparacion: list[ResultadoMetodo]
    hipervolumen: np.ndarray
    segundos: dict[str, float]

    def metodo(self, nombre: str) -> ResultadoMetodo:
        return next(r for r in self.comparacion if r.nombre == nombre)


def nombre_kanan(clave: str) -> str:
    return f"Kanan · {NOMBRES[clave].lower()}"


def construir_sistema(config: Config) -> Sistema:
    mapa = construir_mapa(config.mapa)
    trazador = TrazadorBrechas(mapa, config.brechas)
    simulador = SimuladorFuego(mapa, config.fuego)
    evaluador = Evaluador(mapa, simulador, trazador, cat.pesos_zonas(config.pesos_zonas))
    # Dos sorteos independientes: el AG nunca ve los escenarios de prueba.
    rng_entrenamiento, rng_prueba = np.random.default_rng(config.escenarios.semilla).spawn(2)
    e = config.escenarios
    return Sistema(
        config, mapa, trazador, simulador, evaluador,
        generar_escenarios(mapa, e, e.n_entrenamiento, rng_entrenamiento),
        generar_escenarios(mapa, e, e.n_prueba, rng_prueba),
    )  # fmt: skip


def optimizar(sistema: Sistema, avisar: Avisar = print) -> ResultadoAG:
    config = sistema.config
    inferior, superior = sistema.trazador.limites()
    periodicos = np.tile([False, False, True, False], config.brechas.k)
    nsga = NSGA2(config.ag, inferior, superior, tam_bloque=GENES_POR_BRECHA,
                 periodicos=periodicos, reparar=sistema.trazador.reparar)  # fmt: skip
    cada = max(1, config.ag.generaciones // 10)

    def al_avanzar(generacion: int, total: int) -> None:
        if generacion % cada == 0 or generacion == total:
            avisar(f"  generación {generacion}/{total}")

    return nsga.ejecutar(sistema.evaluador.aptitud(sistema.entrenamiento), al_avanzar)


def validar(
    sistema: Sistema,
    ag: ResultadoAG,
    planes: np.ndarray,
    objetivos: np.ndarray,
    elegidos: dict[str, int],
) -> list[ResultadoMetodo]:
    """Mide los métodos de referencia y los planes de Kanan en los escenarios de prueba."""
    config, trazador = sistema.config, sistema.trazador
    rng = np.random.default_rng(config.ag.semilla + 1)
    metodos: dict[str, np.ndarray | None] = {
        SIN_BRECHAS: None,
        AL_AZAR: referencias.planes_al_azar(trazador, config.validacion.n_planes_azar, rng),
        POBLADOS: referencias.plan_alrededor_de_poblados(trazador, config.escenarios),
    }
    if config.validacion.busqueda_aleatoria:
        candidatos, obj = referencias.busqueda_aleatoria(
            trazador, sistema.evaluador.aptitud(sistema.entrenamiento), ag.evaluaciones, rng
        )
        metodos[BUSQUEDA] = candidatos[int(np.argmin(obj[:, AREA]))]
    kanan = {nombre_kanan(clave): planes[i] for clave, i in elegidos.items()}
    metodos.update(kanan)
    return comparar(sistema.evaluador, sistema.prueba, metodos, kanan=tuple(kanan))


def ejecutar(config: Config, avisar: Avisar = print) -> ResultadoCorrida:
    """Corre el AG y la validación; no escribe archivos."""
    segundos: dict[str, float] = {}
    inicio = time.perf_counter()
    sistema = construir_sistema(config)
    # Una evaluación mínima compila el simulador antes de cronometrar.
    sistema.evaluador.medir(sistema.trazador.poblacion_aleatoria(2, np.random.default_rng(0)),
                            sistema.prueba.uno(0))  # fmt: skip
    segundos["preparacion"] = time.perf_counter() - inicio

    avisar(
        f"Optimizando: {config.ag.poblacion} individuos × {config.ag.generaciones} generaciones "
        f"× {len(sistema.entrenamiento)} escenarios"
    )
    inicio = time.perf_counter()
    ag = optimizar(sistema, avisar)
    segundos["optimizacion"] = time.perf_counter() - inicio
    planes, objetivos = ag.frente()
    elegidos = elegir_planes(objetivos)

    avisar(f"Validando en {len(sistema.prueba)} escenarios de prueba")
    inicio = time.perf_counter()
    comparacion = validar(sistema, ag, planes, objetivos, elegidos)
    segundos["validacion"] = time.perf_counter() - inicio

    return ResultadoCorrida(
        sistema, ag, planes, objetivos, elegidos, comparacion,
        hipervolumen_por_generacion(ag.historial), segundos,
    )  # fmt: skip


def _escenario_de_muestra(sistema: Sistema, brechas: np.ndarray) -> int:
    """Un incendio de prueba grande y donde el plan sí cambia el resultado."""
    sin = sistema.evaluador.medir_sin_brechas(sistema.prueba).area_ha[0]
    con = sistema.evaluador.medir(brechas, sistema.prueba).area_ha[0]
    candidatos = np.flatnonzero(sin >= np.percentile(sin, 60))
    return int(candidatos[np.argmax((sin - con)[candidatos])])


def _parametros(config: Config, resultado: ResultadoCorrida) -> list[tuple[str, str]]:
    m, b, f, e, a = config.mapa, config.brechas, config.fuego, config.escenarios, config.ag
    hectareas = m.filas * m.columnas * m.tam_celda_m**2 / 10_000
    tiempos = resultado.segundos
    return [
        ("Mapa", f"{m.tipo}, {m.filas} × {m.columnas} celdas de {m.tam_celda_m:.0f} m "
                 f"({hectareas:,.0f} ha), semilla {m.semilla}"),
        ("Brechas", f"K = {b.k}, de {b.longitud_min_m:.0f} a {b.longitud_max_m:.0f} m, "
                    f"ancho {b.ancho_m:.0f} m"),
        ("Presupuesto", f"{b.presupuesto:,.0f} pesos"),
        ("Fuego", f"p_h = {f.p_h}, c1 = {f.c1}, c2 = {f.c2}, a = {f.a_pendiente}, "
                  f"máximo {f.duracion_max} pasos"),
        ("Viento", f"{e.viento_vel_min:.0f} a {e.viento_vel_max:.0f} m/s, hacia "
                   f"{e.viento_dir_min:.0f}° a {e.viento_dir_max:.0f}° (azimut)"),
        ("Escenarios", f"{e.n_entrenamiento} de entrenamiento, {e.n_prueba} de prueba, "
                       f"semilla {e.semilla}"),
        ("Algoritmo genético", f"población {a.poblacion}, {a.generaciones} generaciones, "
                               f"cruza {a.p_cruza}, η cruza {a.eta_cruza}, "
                               f"η mutación {a.eta_mutacion}, semilla {a.semilla}"),
        ("Evaluaciones", f"{resultado.ag.evaluaciones:,} planes "
                         f"({resultado.ag.evaluaciones * e.n_entrenamiento:,} incendios)"),
        ("Tiempo", f"optimización {tiempos['optimizacion']:.1f} s, "
                   f"validación {tiempos['validacion']:.1f} s"),
    ]  # fmt: skip


NOTAS = [
    "El mapa es sintético: imita relieve, vegetación, poblados y caminos del área, pero no es "
    "La Sepultura real.",
    "Los parámetros del fuego (p_h, c1, c2, a) son los publicados por Alexandridis et al. "
    "(2008); los de cada tipo de vegetación, los costos y los valores ecológicos son supuestos.",
    "Cada paso del autómata no equivale a un tiempo real calibrado; la duración máxima "
    "representa el tiempo hasta que el incendio se combate.",
    "Una celda mide 100 m y una brecha real unos 10 m: la brecha se modela como la celda "
    "completa sin combustible.",
    "El costo se mide en pesos con tarifas supuestas por metro; sirve para comparar planes, "
    "no como presupuesto de obra.",
]


def guardar_salidas(resultado: ResultadoCorrida, carpeta: Path, avisar: Avisar = print) -> Path:
    """Escribe figuras, animaciones, tablas, resumen y el reporte. Devuelve la ruta del reporte."""
    carpeta.mkdir(parents=True, exist_ok=True)
    sistema, config = resultado.sistema, resultado.sistema.config
    mapa, trazador, simulador = sistema.mapa, sistema.trazador, sistema.simulador
    colores = dict(zip(resultado.elegidos, estilo.COLORES_PLANES, strict=True))
    base = resultado.metodo(SIN_BRECHAS)

    avisar("Generando figuras")
    figuras = {
        nombre: f"{nombre}.png"
        for nombre in ("mapa", "riesgo", "evolucion", "hipervolumen", "pareto", "comparacion",
                       "cajas")  # fmt: skip
    }
    mapas.figura_mapa(mapa, carpeta / figuras["mapa"])
    mapas.figura_riesgo(mapa, carpeta / figuras["riesgo"])
    graficas.figura_evolucion(resultado.ag.historial, carpeta / figuras["evolucion"])
    graficas.figura_hipervolumen(resultado.hipervolumen, carpeta / figuras["hipervolumen"])
    graficas.figura_pareto(
        resultado.frente_objetivos,
        {NOMBRES[c]: (i, colores[c]) for c, i in resultado.elegidos.items()},
        carpeta / figuras["pareto"],
    )
    graficas.figura_comparacion(resultado.comparacion, carpeta / figuras["comparacion"])
    graficas.figura_cajas(resultado.comparacion, carpeta / figuras["cajas"])

    prob_sin = simulador.probabilidad_quema(None, sistema.prueba)
    planes_reporte, filas_genes = [], []
    for clave, indice in resultado.elegidos.items():
        avisar(f"Generando mapas y animación: {NOMBRES[clave]}")
        cromosoma = resultado.frente_planes[indice : indice + 1]
        brechas = trazador.brechas(cromosoma)[0]
        mascara = trazador.trazar(cromosoma).mascaras[0]
        archivos = {
            "mapa": f"plan_{clave}_mapa.png",
            "probabilidad": f"plan_{clave}_probabilidad.png",
            "animacion": f"plan_{clave}_incendio.gif",
        }
        mapas.figura_mapa(mapa, carpeta / archivos["mapa"], brechas, f"Plan: {NOMBRES[clave]}")
        mapas.figura_probabilidad(
            mapa, prob_sin, simulador.probabilidad_quema(mascara, sistema.prueba), brechas,
            f"Probabilidad de quema · {NOMBRES[clave]}", carpeta / archivos["probabilidad"],
        )  # fmt: skip
        muestra = _escenario_de_muestra(sistema, cromosoma)
        mapas.animar_incendio(
            mapa,
            simulador.simular(None, sistema.prueba, muestra).t_ignicion,
            simulador.simular(mascara, sistema.prueba, muestra).t_ignicion,
            brechas,
            f"{NOMBRES[clave]} · escenario de prueba {muestra} · viento "
            f"{sistema.prueba.viento_vel[muestra]:.1f} m/s hacia "
            f"{sistema.prueba.viento_dir[muestra]:.0f}°",
            carpeta / archivos["animacion"],
        )
        genes = tablas.filas_brechas(NOMBRES[clave], brechas)
        filas_genes += genes
        en_prueba = resultado.metodo(nombre_kanan(clave)).medicion.objetivos()[0]
        planes_reporte.append(
            PlanReporte(
                NOMBRES[clave], colores[clave], DESCRIPCIONES[clave],
                tuple(resultado.frente_objetivos[indice]), tuple(en_prueba), genes,
                archivos["mapa"], archivos["probabilidad"], archivos["animacion"],
            )  # fmt: skip
        )

    filas_comparacion = tablas.filas_comparacion(resultado.comparacion, base)
    tablas.escribir_csv(filas_comparacion, carpeta / "comparacion.csv")
    tablas.escribir_csv(filas_genes, carpeta / "planes_brechas.csv")
    tablas.escribir_csv(
        tablas.filas_frente(resultado.frente_planes, resultado.frente_objetivos),
        carpeta / "frente_pareto.csv",
    )
    historial = resultado.ag.historial
    np.savez_compressed(
        carpeta / "historial.npz",
        objetivos=historial.objetivos, violacion=historial.violacion, rangos=historial.rangos,
        hipervolumen=resultado.hipervolumen,
    )  # fmt: skip
    (carpeta / "config_usada.yaml").write_text(
        yaml.safe_dump(config.a_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    mejor = resultado.metodo(nombre_kanan(MENOR_AREA))
    azar = resultado.metodo(AL_AZAR)
    resumen = {
        "objetivos": list(OBJETIVOS),
        "planes_en_el_frente": len(resultado.frente_planes),
        "evaluaciones": resultado.ag.evaluaciones,
        "segundos": {k: round(v, 2) for k, v in resultado.segundos.items()},
        "hipervolumen_final": round(float(resultado.hipervolumen[-1]), 4),
        "comparacion": filas_comparacion,
    }
    (carpeta / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    supera = mejor.area_media < azar.area_media
    conclusion = (
        f"Con el mismo presupuesto, el plan de menor área de Kanan deja arder "
        f"{mejor.area_media:,.0f} ha en promedio en escenarios que nunca vio, contra "
        f"{base.area_media:,.0f} ha sin brechas y {azar.area_media:,.0f} ha con brechas al azar. "
        + ("" if supera else "En esta corrida Kanan no superó a las brechas al azar. ")
        + f"En los escenarios de entrenamiento ese mismo plan obtuvo "
        f"{resultado.frente_objetivos[resultado.elegidos[MENOR_AREA], AREA]:,.0f} ha; la "
        f"diferencia mide cuánto se ajustó el algoritmo a los incendios que vio."
    )
    datos = DatosReporte(
        cifras=[
            (f"{mejor.reduccion_frente_a(base):.0%}", "menos área quemada que sin brechas"),
            (f"{mejor.reduccion_frente_a(azar):.0%}", "menos que con brechas al azar"),
            (f"{len(resultado.frente_planes)}", "planes en el frente de Pareto"),
            (f"{resultado.segundos['optimizacion']:.0f} s", "de optimización"),
        ],
        conclusion=conclusion,
        parametros=_parametros(config, resultado),
        figuras=figuras,
        planes=planes_reporte,
        comparacion=filas_comparacion,
        metodos_kanan={r.nombre for r in resultado.comparacion if r.es_kanan},
        notas=NOTAS,
    )
    ruta = carpeta / "reporte.html"
    generar_reporte(datos, ruta)
    return ruta
