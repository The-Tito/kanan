"""Aplicación interactiva de Kanan.

Se abre con ``kanan app``. Corre el algoritmo con los parámetros de la barra lateral y deja
explorar el resultado sin generar archivos: comparación con los métodos de referencia, cada
plan del frente de Pareto sobre el mapa, incendios simulados paso a paso y la evolución.

Esta capa no calcula nada propio: llama a ``aplicacion.corrida`` y dibuja con ``salidas``.
"""

from __future__ import annotations

import csv
import io
from dataclasses import replace

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from kanan.aplicacion.corrida import (
    AL_AZAR,
    SIN_BRECHAS,
    ResultadoCorrida,
    ejecutar,
    filas_planes_elegidos,
    nombre_kanan,
)
from kanan.config import Config
from kanan.dominio.mapa_sintetico import construir_mapa
from kanan.optimizacion.aptitud import AREA, COSTO, ETIQUETAS, OBJETIVOS
from kanan.optimizacion.seleccion import MENOR_AREA, NOMBRES
from kanan.salidas import estilo, graficas, mapas, tablas
from kanan.salidas.reporte import ENLACE_ZONA_REAL, MAPA_ZONA_REAL, ZONA_REAL

PREAJUSTES = {
    "Rápida (unos 10 s)": {"poblacion": 40, "generaciones": 40, "entrenamiento": 100,
                           "prueba": 200, "azar": 10, "busqueda": False},
    "Completa (cerca de 1 min)": {"poblacion": 100, "generaciones": 200, "entrenamiento": 300,
                                  "prueba": 500, "azar": 30, "busqueda": True},
}  # fmt: skip
OTRO_PLAN = "Otro plan del frente"
SELECCIONADO = "Seleccionado"


def mostrar(figura) -> None:
    """Muestra una figura de matplotlib y la libera."""
    st.pyplot(figura, width="stretch")
    plt.close(figura)


def a_csv(filas: list[tablas.Fila]) -> str:
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=list(filas[0]))
    escritor.writeheader()
    escritor.writerows(filas)
    return salida.getvalue()


# --- Barra lateral ----------------------------------------------------------------------


def barra_lateral() -> tuple[Config, bool]:
    """Entradas del sistema. Devuelve la configuración y si se pidió ejecutar."""
    base = Config()
    with st.sidebar:
        st.header("Kanan")
        st.caption("Brechas cortafuego con NSGA-II")
        nombre = st.radio("Tamaño de la corrida", list(PREAJUSTES), key="preajuste")
        pre = PREAJUSTES[nombre]
        n = list(PREAJUSTES).index(nombre)  # cambia las claves para reiniciar los campos
        pulsado = st.button("Ejecutar", type="primary", width="stretch", key="ejecutar")

        with st.expander("Brechas y presupuesto", expanded=True):
            presupuesto = st.number_input("Presupuesto (pesos)", 50_000, 2_000_000,
                                          int(base.brechas.presupuesto), 25_000,
                                          key="presupuesto")  # fmt: skip
            k = st.slider("Número de brechas (K)", 2, 16, base.brechas.k, key="k")
            lon_min, lon_max = st.slider(
                "Longitud de cada brecha (m)", 100, 5000,
                (int(base.brechas.longitud_min_m), int(base.brechas.longitud_max_m)), 100,
                key="longitud",
            )  # fmt: skip
        with st.expander("Viento y fuego"):
            vel_min, vel_max = st.slider(
                "Velocidad del viento (m/s)", 0.0, 20.0,
                (base.escenarios.viento_vel_min, base.escenarios.viento_vel_max), 0.5,
                key="viento_vel",
            )  # fmt: skip
            dir_min = st.slider("Viento hacia: desde (azimut °)", 0, 360,
                                int(base.escenarios.viento_dir_min), 5, key="dir_min")  # fmt: skip
            dir_max = st.slider("Viento hacia: hasta (azimut °)", 0, 360,
                                int(base.escenarios.viento_dir_max), 5, key="dir_max")  # fmt: skip
            st.caption("0° es norte y 90° es este. El rango puede cruzar el norte.")
            duracion = st.slider("Duración máxima del incendio (pasos)", 10, 120,
                                 base.fuego.duracion_max, key="duracion")  # fmt: skip
        with st.expander("Algoritmo genético"):
            poblacion = st.number_input("Población (par)", 4, 400, pre["poblacion"], 2,
                                        key=f"poblacion-{n}")  # fmt: skip
            generaciones = st.number_input("Generaciones", 1, 1000, pre["generaciones"], 10,
                                           key=f"generaciones-{n}")  # fmt: skip
            entrenamiento = st.number_input("Escenarios de entrenamiento", 5, 1000,
                                            pre["entrenamiento"], 10,
                                            key=f"entrenamiento-{n}")  # fmt: skip
            prueba = st.number_input("Escenarios de prueba", 5, 2000, pre["prueba"], 50,
                                     key=f"prueba-{n}")  # fmt: skip
            semilla = st.number_input("Semilla", 0, 999_999, base.ag.semilla, key="semilla")
            busqueda = st.checkbox(
                "Comparar con búsqueda aleatoria", pre["busqueda"], key=f"busqueda-{n}",
                help="Repite todas las evaluaciones del algoritmo con planes al azar; "
                "duplica el tiempo.",
            )

    config = replace(
        base,
        brechas=replace(base.brechas, presupuesto=float(presupuesto), k=int(k),
                        longitud_min_m=float(lon_min), longitud_max_m=float(lon_max)),
        fuego=replace(base.fuego, duracion_max=int(duracion)),
        escenarios=replace(base.escenarios, viento_vel_min=vel_min, viento_vel_max=vel_max,
                           viento_dir_min=float(dir_min), viento_dir_max=float(dir_max),
                           n_entrenamiento=int(entrenamiento), n_prueba=int(prueba)),
        ag=replace(base.ag, poblacion=int(poblacion), generaciones=int(generaciones),
                   semilla=int(semilla)),
        validacion=replace(base.validacion, n_planes_azar=pre["azar"],
                           busqueda_aleatoria=busqueda),
    )  # fmt: skip
    return config, pulsado


def correr(config: Config) -> ResultadoCorrida | None:
    try:
        config.validar()
    except ValueError as error:
        st.error(f"Configuración no válida: {error}")
        return None
    barra = st.progress(0.0, text="Preparando el simulador…")

    def progreso(generacion: int, total: int) -> None:
        barra.progress(0.8 * generacion / total, text=f"Generación {generacion} de {total}")

    def avisar(mensaje: str) -> None:
        if mensaje.startswith("Validando"):
            barra.progress(0.85, text=f"{mensaje}…")

    resultado = ejecutar(config, avisar, progreso)
    barra.empty()
    return resultado


# --- Pestañas ---------------------------------------------------------------------------


def pestana_resultado(resultado: ResultadoCorrida) -> None:
    base = resultado.metodo(SIN_BRECHAS)
    azar = resultado.metodo(AL_AZAR)
    mejor = resultado.metodo(nombre_kanan(MENOR_AREA))
    entrenamiento = resultado.frente_objetivos[resultado.elegidos[MENOR_AREA], AREA]
    a, b, c, d = st.columns(4)
    a.metric("Kanan (menor área)", f"{mejor.area_media:,.0f} ha",
             f"{-mejor.reduccion_frente_a(base):.0%} vs. sin brechas", delta_color="inverse")  # fmt: skip
    b.metric("Brechas al azar", f"{azar.area_media:,.0f} ha",
             f"{-azar.reduccion_frente_a(base):.0%} vs. sin brechas", delta_color="inverse")  # fmt: skip
    c.metric("Planes en el frente", len(resultado.frente_planes))
    d.metric("Optimización", f"{resultado.segundos['optimizacion']:.1f} s")
    d.caption(f"{resultado.ag.evaluaciones:,} planes evaluados")
    if mejor.area_media >= azar.area_media:
        st.warning("En esta corrida Kanan no superó a las brechas al azar. Prueba con más "
                   "generaciones o más escenarios de entrenamiento.")  # fmt: skip
    st.caption(
        f"Todos los métodos usan el mismo presupuesto y se miden en "
        f"{len(resultado.sistema.prueba)} incendios que el algoritmo nunca vio. En los de "
        f"entrenamiento, el mejor plan obtuvo {entrenamiento:,.0f} ha: la diferencia mide cuánto "
        f"se ajustó a los incendios que vio."
    )
    mostrar(graficas.figura_comparacion(resultado.comparacion))
    with st.expander("Tabla y dispersión por escenario"):
        st.dataframe(tablas.filas_comparacion(resultado.comparacion, base), width="stretch",
                     hide_index=True)  # fmt: skip
        mostrar(graficas.figura_cajas(resultado.comparacion))


def grafica_frente(resultado: ResultadoCorrida, plan: int, eje_x: str, eje_y: str):
    """Frente de Pareto con selección por clic; devuelve el evento de Streamlit."""
    colores = dict(zip(resultado.elegidos, estilo.COLORES_PLANES, strict=True))
    por_indice = {i: NOMBRES[c] for c, i in resultado.elegidos.items()}
    datos = pd.DataFrame(resultado.frente_objetivos, columns=[ETIQUETAS[o] for o in OBJETIVOS])
    datos["plan"] = np.arange(len(datos))
    datos["grupo"] = [por_indice.get(i, OTRO_PLAN) for i in datos["plan"]]
    datos.loc[plan, "grupo"] = SELECCIONADO
    dominio = [OTRO_PLAN, *(NOMBRES[c] for c in colores), SELECCIONADO]
    rango = [estilo.REFERENCIA, *colores.values(), estilo.TINTA]
    clic = alt.selection_point(name="clic", fields=["plan"], on="click", empty=False)
    grafica = (
        alt.Chart(datos)
        .mark_circle(opacity=1, stroke="white", strokeWidth=1.5)
        .encode(
            x=alt.X(ETIQUETAS[eje_x], scale=alt.Scale(zero=False)),
            y=alt.Y(ETIQUETAS[eje_y], scale=alt.Scale(zero=False)),
            color=alt.Color("grupo", scale=alt.Scale(domain=dominio, range=rango),
                            legend=alt.Legend(title=None, orient="bottom", direction="vertical",
                                              columns=2)),
            size=alt.Size("grupo", legend=None,
                          scale=alt.Scale(domain=dominio, range=[70, 220, 220, 220, 320])),
            tooltip=["plan", *(alt.Tooltip(ETIQUETAS[o], format=",.1f") for o in OBJETIVOS)],
        )
        .add_params(clic)
        .properties(height=430)
    )  # fmt: skip
    return st.altair_chart(grafica, on_select="rerun", key="frente", width="stretch")


def pestana_planes(resultado: ResultadoCorrida) -> None:
    sistema = resultado.sistema
    mapa, trazador, simulador = sistema.mapa, sistema.trazador, sistema.simulador
    cache = st.session_state["cache"]
    n = len(resultado.frente_planes)
    st.session_state.setdefault("plan", resultado.elegidos[MENOR_AREA])

    st.markdown("**Elige un plan** con los botones, con el selector, o haciendo clic en un punto.")
    botones = st.columns(len(resultado.elegidos) + 1)
    for columna, (clave, indice) in zip(botones, resultado.elegidos.items(), strict=False):
        if columna.button(NOMBRES[clave], key=f"elegir-{clave}", width="stretch"):
            st.session_state["plan"] = indice
    botones[-1].number_input("Plan del frente", 0, n - 1, key="plan", label_visibility="collapsed")
    plan = int(st.session_state["plan"])

    izquierda, derecha = st.columns([1.15, 1])
    with izquierda:
        ejes = st.columns(2)
        eje_x = ejes[0].selectbox("Eje horizontal", OBJETIVOS, 0, format_func=ETIQUETAS.get)
        eje_y = ejes[1].selectbox("Eje vertical", OBJETIVOS, 2, format_func=ETIQUETAS.get)
        evento = grafica_frente(resultado, plan, eje_x, eje_y)
        puntos = evento.selection.get("clic", []) if evento else []
        if puntos and puntos != st.session_state.get("ultimo_clic"):
            st.session_state["ultimo_clic"] = puntos
            st.session_state["plan_pendiente"] = int(puntos[0]["plan"])
            st.rerun()

    cromosoma = resultado.frente_planes[plan : plan + 1]
    brechas = trazador.brechas(cromosoma)[0]
    trazado = trazador.trazar(cromosoma)
    mascara = trazado.mascaras[0]
    if plan not in cache:
        cache[plan] = sistema.evaluador.medir(cromosoma, sistema.prueba)
    medicion = cache[plan]
    if "sin" not in cache:
        cache["sin"] = sistema.evaluador.medir_sin_brechas(sistema.prueba)
    sin = cache["sin"]

    with derecha:
        mostrar(mapas.figura_mapa(mapa, None, brechas, f"Plan {plan} de {n - 1}"))

    en_prueba = medicion.objetivos()[0]
    reduccion = 1 - en_prueba[AREA] / sin.objetivos()[0][AREA]
    a, b, c, d = st.columns(4)
    a.metric("Área quemada (prueba)", f"{en_prueba[AREA]:,.0f} ha", f"{-reduccion:.0%}",
             delta_color="inverse")  # fmt: skip
    b.metric("Valor afectado (prueba)", f"{en_prueba[1]:,.0f}")
    c.metric("Costo", f"${en_prueba[COSTO]:,.0f}")
    c.caption(f"{en_prueba[COSTO] / trazador.config.presupuesto:.0%} del presupuesto")
    d.metric("Impacto ecológico", f"{en_prueba[3]:.2f} ha eq.")
    with st.expander("Genes de las brechas de este plan"):
        st.dataframe(tablas.filas_brechas(f"Plan {plan}", brechas), width="stretch",
                     hide_index=True)  # fmt: skip

    st.subheader("Simular un incendio")
    diferencia = sin.area_ha[0] - medicion.area_ha[0]
    orden = np.argsort(-diferencia)
    escenario = st.selectbox(
        "Escenario de prueba (ordenados por cuánto ayuda el plan)",
        orden.tolist(),
        format_func=lambda i: (
            f"#{i} · viento {sistema.prueba.viento_vel[i]:.0f} m/s hacia "
            f"{sistema.prueba.viento_dir[i]:.0f}° · sin brechas {sin.area_ha[0][i]:,.0f} ha · "
            f"con el plan {medicion.area_ha[0][i]:,.0f} ha"
        ),
        key=f"escenario-{plan}",
    )
    t_sin = simulador.simular(None, sistema.prueba, escenario).t_ignicion
    t_con = simulador.simular(mascara, sistema.prueba, escenario).t_ignicion
    ultimo = int(max(t_sin.max(), t_con.max()))
    paso = st.slider("Paso de la simulación", 0, max(ultimo, 1), max(ultimo, 1),
                     key=f"paso-{plan}-{escenario}")  # fmt: skip
    figura, ejes_fuego = plt.subplots(1, 2, figsize=(11, 5.2))
    for ax, tiempos, titulo, plan_brechas in ((ejes_fuego[0], t_sin, "Sin brechas", None),
                                              (ejes_fuego[1], t_con, "Con el plan", brechas)):  # fmt: skip
        mapas.dibujar_fondo(ax, mapa, alfa=0.75)
        if plan_brechas is not None:
            mapas.dibujar_brechas(ax, plan_brechas, numerar=False)
        ax.imshow(mapas._capa_fuego(tiempos, paso), extent=mapas._extension_km(mapa),
                  interpolation="nearest", zorder=3)  # fmt: skip
        hectareas = ((tiempos >= 0) & (tiempos <= paso)).sum() * mapa.area_celda_ha
        ax.set_title(f"{titulo} · {hectareas:,.0f} ha")
    mostrar(figura)

    st.subheader("Probabilidad de quema")
    st.caption("Fracción de los escenarios de prueba en que arde cada celda.")
    if "prob_sin" not in cache:
        cache["prob_sin"] = simulador.probabilidad_quema(None, sistema.prueba)
    mostrar(mapas.figura_probabilidad(
        mapa, cache["prob_sin"], simulador.probabilidad_quema(mascara, sistema.prueba), brechas,
        f"Plan {plan}",
    ))  # fmt: skip


def pestana_evolucion(resultado: ResultadoCorrida) -> None:
    colores = dict(zip(resultado.elegidos, estilo.COLORES_PLANES, strict=True))
    st.caption("Valores sobre los escenarios de entrenamiento, generación por generación.")
    mostrar(graficas.figura_evolucion(resultado.ag.historial))
    mostrar(graficas.figura_hipervolumen(resultado.hipervolumen))
    mostrar(graficas.figura_pareto(
        resultado.frente_objetivos,
        {NOMBRES[c]: (i, colores[c]) for c, i in resultado.elegidos.items()},
    ))  # fmt: skip


def pestana_zona(config: Config) -> None:
    mapa = construir_mapa(config.mapa)
    st.caption("El algoritmo trabaja sobre este mapa sintético, con los rasgos de La Sepultura.")
    izquierda, derecha = st.columns(2)
    with izquierda:
        mostrar(mapas.figura_mapa(mapa, None))
    with derecha:
        mostrar(mapas.figura_riesgo(mapa))
    st.subheader("La zona real")
    st.caption(f"{ZONA_REAL}, en Google Maps. Solo es referencia visual: no se calcula sobre "
               f"este terreno. Requiere internet; [abrir en Google Maps]({ENLACE_ZONA_REAL}).")  # fmt: skip
    st.iframe(MAPA_ZONA_REAL, height=460)


def pestana_datos(resultado: ResultadoCorrida) -> None:
    st.caption("Nada se guarda en disco: descarga solo lo que necesites.")
    base = resultado.metodo(SIN_BRECHAS)
    descargas = {
        "comparacion.csv": tablas.filas_comparacion(resultado.comparacion, base),
        "frente_pareto.csv": tablas.filas_frente(resultado.frente_planes,
                                                 resultado.frente_objetivos),
        "planes_brechas.csv": filas_planes_elegidos(resultado),
    }  # fmt: skip
    for columna, (nombre, filas) in zip(st.columns(len(descargas)), descargas.items(),
                                        strict=True):  # fmt: skip
        columna.download_button(nombre, a_csv(filas), nombre, "text/csv", width="stretch")
    st.subheader("Configuración de esta corrida")
    st.json(resultado.sistema.config.a_dict(), expanded=1)
    st.caption("Para el reporte HTML con animaciones: `kanan ejecutar --reporte`.")


# --- Página -----------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(page_title="Kanan", page_icon="🌲", layout="wide")
    estilo.aplicar()
    # Un clic en la gráfica cambia el plan antes de que exista el campo que lo muestra.
    if "plan_pendiente" in st.session_state:
        st.session_state["plan"] = st.session_state.pop("plan_pendiente")

    config, pulsado = barra_lateral()
    if pulsado:
        resultado = correr(config)
        if resultado is not None:
            st.session_state["resultado"] = resultado
            st.session_state["cache"] = {}
            for clave in ("plan", "ultimo_clic"):
                st.session_state.pop(clave, None)

    resultado: ResultadoCorrida | None = st.session_state.get("resultado")
    st.title("Kanan")
    st.caption("Dónde construir brechas cortafuego, decidido por un algoritmo genético "
               "multiobjetivo. Prototipo sobre un mapa sintético: no es una recomendación "
               "operativa.")  # fmt: skip
    if resultado is None:
        st.info("Ajusta los parámetros en la barra lateral y pulsa **Ejecutar**.")
        pestana_zona(config)
        return

    # Un selector con estado en lugar de st.tabs: la sección sobrevive a cada recarga (un
    # clic en la gráfica recarga la página) y solo se dibuja la que está a la vista.
    secciones = {
        "Resultado": lambda: pestana_resultado(resultado),
        "Explorar planes": lambda: pestana_planes(resultado),
        "Evolución": lambda: pestana_evolucion(resultado),
        "Zona de estudio": lambda: pestana_zona(resultado.sistema.config),
        "Datos": lambda: pestana_datos(resultado),
    }
    activa = st.radio("Sección", list(secciones), horizontal=True, key="seccion",
                      label_visibility="collapsed")  # fmt: skip
    st.divider()
    secciones[activa]()


main()
