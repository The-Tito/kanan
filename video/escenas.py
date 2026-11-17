"""Las diez escenas del video: qué se dice y qué se ve en cada frase.

Todo lo que se dibuja sale del código y de los datos reales de Kanan (mapa, simulador,
trazador, historial del NSGA-II); no hay ilustraciones hechas a mano.
"""

from __future__ import annotations

import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch, Rectangle

from kanan.aplicacion.corrida import Sistema, _escenario_de_muestra
from kanan.config import ConfigBrechas
from kanan.dominio import catalogos as cat
from kanan.dominio.plan import ANGULO, LONGITUD, TrazadorBrechas, X, Y
from kanan.optimizacion.aptitud import AREA, COSTO
from kanan.optimizacion.nsga2 import (
    distancia_apinamiento,
    matriz_dominancia,
    ordenamiento_no_dominado,
)
from kanan.optimizacion.seleccion import EQUILIBRADO, MENOR_AREA, MENOR_COSTO, NOMBRES
from kanan.salidas import estilo, mapas
from kanan.simulacion.automata import D_COL, D_FILA, factor_viento
from video.datos import Corrida
from video.motor import Escena, Tiempo

RELACION = 9 / 16
"""Alto entre ancho del cuadro: un eje cuadrado de alto h mide h * RELACION de ancho."""
NOMBRES_ZONAS = {"poblado": "Poblado", "infraestructura": "Infraestructura",
                 "zona_nucleo": "Zona núcleo", "cultivo": "Cultivo"}  # fmt: skip
RUMBOS = ("norte", "noreste", "este", "sureste", "sur", "suroeste", "oeste", "noroeste")
T, S, G = estilo.TINTA, estilo.TINTA_SECUNDARIA, estilo.REFERENCIA
AZUL, NARANJA, AQUA = estilo.COLORES_PLANES


# --- Piezas de dibujo -------------------------------------------------------------------


def texto(fig: Figure, x: float, y: float, s: str, tam: float = 22, color: str = T, **kw):
    kw.setdefault("va", "center")
    return fig.text(x, y, s, fontsize=tam, color=color, **kw)


def lista(fig: Figure, x: float, y: float, renglones: list[str], visibles: int | None = None,
          tam: float = 22, paso: float = 0.085, color: str = T) -> None:  # fmt: skip
    for i, renglon in enumerate(renglones[:visibles]):
        texto(fig, x, y - i * paso, "•", tam, AZUL, fontweight="bold")
        texto(fig, x + 0.018, y - i * paso, renglon, tam, color)


def tarjeta(fig: Figure, x: float, y: float, ancho: float, valor: str, pie: str,
            color: str = T, tam: float = 54) -> None:  # fmt: skip
    fig.add_artist(FancyBboxPatch((x, y), ancho, 0.26, boxstyle="round,pad=0,rounding_size=0.012",
                                  fc="white", ec=estilo.REJILLA, lw=1.5,
                                  transform=fig.transFigure))  # fmt: skip
    texto(fig, x + 0.02, y + 0.17, valor, tam, color, fontweight="bold")
    texto(fig, x + 0.02, y + 0.065, pie, 18, S, linespacing=1.3)


def eje_mapa(fig: Figure, sistema: Sistema, x: float, y: float, alto: float, alfa: float = 1.0):
    """Eje cuadrado con el mapa de fondo; (x, y) es su esquina inferior izquierda."""
    ax = fig.add_axes((x, y, alto * RELACION, alto))
    mapas.dibujar_fondo(ax, sistema.mapa, alfa)
    ax.set_axis_off()
    return ax


def eje_imagen(fig: Figure, sistema: Sistema, x: float, y: float, alto: float, imagen, **kw):
    ax = fig.add_axes((x, y, alto * RELACION, alto))
    ax.imshow(imagen, extent=mapas._extension_km(sistema.mapa), interpolation="nearest", **kw)
    ax.set_axis_off()
    return ax


def trazo_brechas(ax, brechas: np.ndarray, colores, grosor: float = 3.2, alfa: float = 1.0):
    """Segmentos con borde blanco; ``colores`` es uno solo o uno por brecha."""
    if isinstance(colores, str):
        colores = [colores] * len(brechas)
    for brecha, color in zip(brechas, colores, strict=True):
        angulo = np.radians(brecha[ANGULO])
        x0, y0 = brecha[X] / 1000.0, brecha[Y] / 1000.0
        xs = [x0, x0 + np.cos(angulo) * brecha[LONGITUD] / 1000.0]
        ys = [y0, y0 + np.sin(angulo) * brecha[LONGITUD] / 1000.0]
        ax.plot(xs, ys, color="white", lw=grosor + 2.6, solid_capstyle="round", zorder=5,
                alpha=alfa)  # fmt: skip
        ax.plot(xs, ys, color=color, lw=grosor, solid_capstyle="round", zorder=6, alpha=alfa)


def capa_fuego(ax, sistema: Sistema, t_ignicion: np.ndarray, paso: int) -> None:
    ax.imshow(mapas._capa_fuego(t_ignicion, paso), extent=mapas._extension_km(sistema.mapa),
              interpolation="nearest", zorder=3)  # fmt: skip


def eje_dispersion(fig: Figure, rect, xlabel: str, ylabel: str):
    ax = fig.add_axes(rect)
    ax.set_xlabel(xlabel, fontsize=17)
    ax.set_ylabel(ylabel, fontsize=17)
    ax.tick_params(labelsize=14)
    return ax


def rejilla_vecinas(fig: Figure, x: float, y: float, alto: float, prob: np.ndarray, titulo: str):
    """Celda en llamas al centro y la probabilidad de encender a cada vecina."""
    ax = fig.add_axes((x, y, alto * RELACION, alto))
    valores = np.zeros((3, 3))
    for d in range(8):
        valores[1 + D_FILA[d], 1 + D_COL[d]] = prob[d]
    ax.imshow(valores, cmap="Oranges", vmin=0, vmax=1.25)
    ax.add_patch(Rectangle((0.5, 0.5), 1, 1, fc=estilo.COLOR_LLAMAS, ec="white", lw=3))
    ax.text(1, 1, "en\nllamas", ha="center", va="center", color="white", fontsize=17,
            fontweight="bold")  # fmt: skip
    for d in range(8):
        ax.text(1 + D_COL[d], 1 + D_FILA[d], f"{prob[d]:.0%}", ha="center", va="center",
                fontsize=24, fontweight="bold", color="white" if prob[d] > 0.6 else T)  # fmt: skip
    for k in (0.5, 1.5):
        ax.axhline(k, color="white", lw=3)
        ax.axvline(k, color="white", lw=3)
    ax.set_axis_off()
    texto(fig, x + alto * RELACION / 2, y + alto + 0.035, titulo, 20, T, ha="center",
          fontweight="bold")  # fmt: skip
    return ax


# --- Escenas ----------------------------------------------------------------------------


def construir_escenas(sistema: Sistema, corrida: Corrida) -> list[Escena]:
    mapa, trazador, simulador = sistema.mapa, sistema.trazador, sistema.simulador
    config = sistema.config
    presupuesto = config.brechas.presupuesto
    historia = corrida.objetivos_por_generacion
    indice_mejor = corrida.elegidos[MENOR_AREA]
    plan_mejor = corrida.frente_planes[indice_mejor : indice_mejor + 1]
    brechas_mejor = trazador.brechas(plan_mejor)[0]
    mascara_mejor = trazador.trazar(plan_mejor).mascaras[0]
    muestra = _escenario_de_muestra(sistema, plan_mejor)
    fuego_libre = simulador.simular(None, sistema.prueba, muestra).t_ignicion
    metodos = {nombre: (area, costo, kanan) for nombre, area, costo, kanan in corrida.comparacion}
    sin_brechas = metodos["Sin brechas"][0]

    # ---- 1. El problema ----
    def portada(fig, _):
        texto(fig, 0.5, 0.60, "Kanan", 120, T, ha="center", fontweight="bold")
        texto(fig, 0.5, 0.43, "cuidar  ·  proteger  ·  vigilar", 34, AZUL, ha="center")
        texto(fig, 0.5, 0.33, "Dónde construir brechas cortafuego, decidido por un algoritmo "
              "genético", 22, S, ha="center")  # fmt: skip

    def cifras(fig, _):
        texto(fig, 0.04, 0.80, "Reserva de la Biosfera La Sepultura, Chiapas · 2025", 26, T,
              fontweight="bold")  # fmt: skip
        tarjeta(fig, 0.04, 0.42, 0.28, "28", "incendios forestales")
        tarjeta(fig, 0.36, 0.42, 0.28, "4,097 ha", "quemadas")
        tarjeta(fig, 0.68, 0.42, 0.28, "108 de 113", "con causa conocida,\nde origen humano")
        texto(fig, 0.04, 0.33, "Fuente: Protección Civil Chiapas, corte al 2 de octubre de 2025. "
              "Las causas son de todo el estado.", 15, estilo.TINTA_TENUE)  # fmt: skip

    def que_es_brecha(fig, _):
        ax = eje_mapa(fig, sistema, 0.04, 0.14, 0.72)
        trazo_brechas(ax, brechas_mejor, estilo.COLOR_BRECHA)
        texto(fig, 0.50, 0.78, "Una brecha cortafuego", 30, T, fontweight="bold")
        lista(fig, 0.50, 0.66, ["Franja sin vegetación que detiene el fuego",
                                "Abrirla cuesta dinero",
                                "Desmonta parte del bosque",
                                "El presupuesto alcanza para pocos kilómetros"])  # fmt: skip

    def donde(fig, avance):
        ax = eje_mapa(fig, sistema, 0.04, 0.14, 0.72)
        i = int(round(avance * 11))
        trazo_brechas(ax, trazador.brechas(corrida.poblacion_inicial[i : i + 1])[0],
                      estilo.COLOR_BRECHA)  # fmt: skip
        texto(fig, 0.50, 0.74, "¿Dónde poner 8 brechas?", 38, T, fontweight="bold")
        texto(fig, 0.50, 0.62, f"Plan al azar número {i + 1}", 24, AZUL)
        lista(fig, 0.50, 0.50, ["Miles de posiciones, ángulos y longitudes",
                                "Un plan solo se conoce simulando incendios"])  # fmt: skip

    problema = Escena("01-problema", "El problema", [
        Tiempo("Kanan significa cuidar, proteger y vigilar en tseltal. Es un programa que decide "
               "dónde construir brechas cortafuego en un bosque.", portada),
        Tiempo("El caso de estudio es la reserva de La Sepultura, en Chiapas. En dos mil "
               "veinticinco tuvo veintiocho incendios y perdió más de cuatro mil hectáreas. "
               "Casi todos los incendios del estado fueron provocados por personas.", cifras),
        Tiempo("Una brecha es una franja sin vegetación que detiene al fuego. Pero abrirla "
               "cuesta dinero, destruye parte del bosque, y el presupuesto solo alcanza para "
               "unos cuantos kilómetros.", que_es_brecha),
        Tiempo("Entonces, ¿dónde conviene ponerlas? Hay miles de combinaciones posibles, y la "
               "única forma de saber si un plan funciona es simular incendios sobre él. Eso es "
               "lo que hace Kanan.", donde, cuadros=12),
    ])  # fmt: skip

    # ---- 2. El mapa ----
    def leyenda_vegetacion(fig, x, y):
        for i, tipo in enumerate(cat.VEGETACION):
            fig.add_artist(Rectangle((x, y - i * 0.062 - 0.016), 0.022, 0.034, fc=tipo.color,
                                     ec=estilo.EJE, transform=fig.transFigure))  # fmt: skip
            texto(fig, x + 0.034, y - i * 0.062, tipo.nombre, 19, S)

    def capa_vegetacion(fig, _):
        eje_mapa(fig, sistema, 0.04, 0.14, 0.72)
        texto(fig, 0.50, 0.80, "Vegetación y densidad", 30, T, fontweight="bold")
        texto(fig, 0.50, 0.73, "80 × 80 celdas de 100 m  ·  6,400 hectáreas", 21, AZUL)
        leyenda_vegetacion(fig, 0.50, 0.63)

    def capa_elevacion(fig, _):
        ax = eje_imagen(fig, sistema, 0.04, 0.14, 0.72, mapa.elevacion, cmap="Greys")
        km = (np.arange(mapa.forma[0]) + 0.5) * mapa.tam_celda_m / 1000.0
        ax.contour(km, km, mapa.elevacion, levels=10, colors="#00000055", linewidths=0.8)
        texto(fig, 0.50, 0.80, "Elevación", 30, T, fontweight="bold")
        texto(fig, 0.50, 0.73, f"De {mapa.elevacion.min():,.0f} a {mapa.elevacion.max():,.0f} "
              "metros (más oscuro = más alto)", 21, AZUL)  # fmt: skip
        lista(fig, 0.50, 0.61, ["De la elevación sale la pendiente",
                                "El fuego sube más rápido de lo que baja",
                                "En pendiente, abrir brecha cuesta más"])  # fmt: skip

    def capa_valor(fig, _):
        ax = eje_mapa(fig, sistema, 0.04, 0.14, 0.72, alfa=0.45)
        colores = ListedColormap(["#00000000"] + [z.color for z in cat.ZONAS_VALOR[1:]])
        ax.imshow(mapa.zona_valor, cmap=colores, vmin=-0.5, vmax=4.5, alpha=0.85, zorder=2,
                  extent=mapas._extension_km(mapa), interpolation="nearest")  # fmt: skip
        texto(fig, 0.50, 0.80, "Zonas de valor", 30, T, fontweight="bold")
        texto(fig, 0.50, 0.73, "Peso de cada hectárea quemada", 21, AZUL)
        for i, zona in enumerate(cat.ZONAS_VALOR[1:]):
            y = 0.62 - i * 0.085
            fig.add_artist(Rectangle((0.50, y - 0.02), 0.022, 0.04, fc=zona.color,
                                     transform=fig.transFigure))  # fmt: skip
            texto(fig, 0.535, y, NOMBRES_ZONAS[zona.nombre], 22, T)
            texto(fig, 0.80, y, f"× {zona.peso:.0f}", 26, T, fontweight="bold")

    def capa_riesgo(fig, _):
        relativo = mapa.prob_ignicion / mapa.prob_ignicion.max()
        eje_imagen(fig, sistema, 0.04, 0.14, 0.72, relativo, cmap="Oranges", vmin=0, vmax=1)
        texto(fig, 0.50, 0.80, "Riesgo de ignición", 30, T, fontweight="bold")
        texto(fig, 0.50, 0.73, "Más oscuro = más probable el inicio de un incendio", 21, AZUL)
        lista(fig, 0.50, 0.61, ["Mayor junto a caminos y parcelas",
                                "De aquí se sortea el inicio de\n   cada incendio simulado"])  # fmt: skip

    el_mapa = Escena("02-mapa", "El mapa: lo que Kanan sabe del terreno", [
        Tiempo("Todo empieza con un mapa dividido en una cuadrícula de ochenta por ochenta "
               "celdas. Cada celda mide cien metros por lado y guarda qué vegetación tiene y "
               "qué tan densa es.", capa_vegetacion),
        Tiempo("También guarda su elevación. Con ella se calcula la pendiente, que importa "
               "porque el fuego sube más rápido de lo que baja.", capa_elevacion),
        Tiempo("Algunas celdas valen más que otras: los poblados, la infraestructura, la zona "
               "núcleo de la reserva y los cultivos. Cada una tiene un peso según su "
               "importancia.", capa_valor),
        Tiempo("Y por último, el riesgo de ignición. Como casi todos los incendios son de origen "
               "humano, es más probable que el fuego empiece cerca de caminos y parcelas.",
               capa_riesgo),
    ])  # fmt: skip

    # ---- 3. El fuego ----
    p_h = config.fuego.p_h
    FORMULA = r"$p_{quema} = p_h\,(1 + p_{veg})\,(1 + p_{den})\;p_{viento}\;p_{pendiente}$"

    def estados(fig, _):
        nombres = [("Sin combustible", "agua o brecha", "#4a90c2"),
                   ("Con combustible", "puede arder", "#9bbf6b"),
                   ("En llamas", "dura un paso", estilo.COLOR_LLAMAS),
                   ("Quemada", "ya no arde", estilo.COLOR_QUEMADO)]  # fmt: skip
        for i, (nombre, pie, color) in enumerate(nombres):
            x = 0.07 + i * 0.225
            fig.add_artist(Rectangle((x, 0.42), 0.17, 0.17 / RELACION, fc=color, ec="white",
                                     lw=3, transform=fig.transFigure))  # fmt: skip
            texto(fig, x + 0.085, 0.36, nombre, 24, T, ha="center", fontweight="bold")
            texto(fig, x + 0.085, 0.30, pie, 19, S, ha="center")
        texto(fig, 0.5, 0.80, "Cada celda está en uno de cuatro estados", 28, T, ha="center",
              fontweight="bold")  # fmt: skip

    def regla(fig, _):
        rejilla_vecinas(fig, 0.10, 0.20, 0.52, np.full(8, p_h), "Sin viento, terreno plano")
        texto(fig, 0.47, 0.72, "La regla de cada paso", 30, T, fontweight="bold")
        lista(fig, 0.47, 0.60, ["Una celda en llamas intenta encender\n   a sus 8 vecinas",
                                "Cada intento tiene una probabilidad",
                                "Después, la celda queda quemada"], paso=0.11)  # fmt: skip
        texto(fig, 0.47, 0.25, f"Probabilidad base  $p_h$ = {p_h}", 22, AZUL)

    def factores(fig, _):
        viento = p_h * factor_viento(np.array([8.0]), np.array([90.0]), config.fuego.c1,
                                     config.fuego.c2)[0]  # fmt: skip
        distancia = np.where(np.arange(8) % 2 == 1, np.sqrt(2.0), 1.0)
        sube = np.tan(np.radians(15.0)) * -D_FILA / distancia
        pendiente = p_h * np.exp(config.fuego.a_pendiente * np.degrees(np.arctan(sube)))
        rejilla_vecinas(fig, 0.08, 0.17, 0.46, np.clip(viento, 0, 1), "Viento de 8 m/s → este")
        rejilla_vecinas(fig, 0.385, 0.17, 0.46, np.clip(pendiente, 0, 1),
                        "Pendiente de 15° ↑ norte")  # fmt: skip
        texto(fig, 0.5, 0.82, FORMULA, 30, T, ha="center")
        lista(fig, 0.68, 0.58, ["Vegetación y densidad\n   de la celda vecina",
                                "A favor del viento sube;\n   en contra, baja",
                                "Cuesta arriba sube"], tam=20, paso=0.13)  # fmt: skip

    def incendio(fig, avance):
        paso = int(round(avance * fuego_libre.max()))
        ax = eje_mapa(fig, sistema, 0.04, 0.14, 0.72, alfa=0.8)
        capa_fuego(ax, sistema, fuego_libre, paso)
        hectareas = ((fuego_libre >= 0) & (fuego_libre <= paso)).sum() * mapa.area_celda_ha
        velocidad = sistema.prueba.viento_vel[muestra]
        rumbo = RUMBOS[int(round(sistema.prueba.viento_dir[muestra] / 45.0)) % 8]
        texto(fig, 0.50, 0.78, "Un escenario de incendio", 30, T, fontweight="bold")
        lista(fig, 0.50, 0.67, ["Un punto de inicio",
                                f"Un viento ({velocidad:.0f} m/s hacia el {rumbo})",
                                "Una semilla que fija el azar"], tam=21, paso=0.075)  # fmt: skip
        texto(fig, 0.50, 0.38, f"Paso {paso}", 26, S)
        texto(fig, 0.50, 0.27, f"{hectareas:,.0f} ha", 66, estilo.COLOR_LLAMAS, fontweight="bold")
        texto(fig, 0.50, 0.19, "quemadas, sin brechas", 20, S)

    el_fuego = Escena("03-fuego", "El fuego: un autómata celular", [
        Tiempo("Para simular un incendio, Kanan usa un autómata celular. Cada celda está en uno "
               "de cuatro estados: sin combustible, con combustible, en llamas, o ya quemada.",
               estados),
        Tiempo("La regla es simple. En cada paso, una celda en llamas intenta encender a cada "
               "una de sus ocho vecinas, con cierta probabilidad, y después queda quemada.",
               regla),
        Tiempo("Esa probabilidad no es fija. Sube si la vecina tiene vegetación densa o muy "
               "inflamable. Sube mucho en la dirección del viento, y baja en contra. Y sube "
               "cuando el fuego va cuesta arriba.", factores),
        Tiempo("Repitiendo esa regla paso a paso, el fuego se extiende por el mapa. Un escenario "
               "de incendio es un punto de inicio, un viento, y una semilla que fija el azar. "
               "Así, el mismo escenario se puede repetir con distintos planes y compararlos "
               "con justicia.", incendio, cuadros=int(fuego_libre.max()) + 1),
    ])  # fmt: skip

    # ---- 4. El plan ----
    def tabla_genes(fig, x, y, resaltar: int | None, visibles: int = 8):
        columnas = ["", "x inicio", "y inicio", "ángulo", "longitud"]
        anchos = [0.0, 0.055, 0.155, 0.255, 0.345]
        for nombre, dx in zip(columnas, anchos, strict=True):
            texto(fig, x + dx, y, nombre, 18, S, fontweight="bold")
        for k, brecha in enumerate(brechas_mejor[:visibles]):
            yy = y - (k + 1) * 0.062
            activo = k == resaltar
            if activo:
                fig.add_artist(Rectangle((x - 0.012, yy - 0.028), 0.45, 0.056, fc="#2a78d622",
                                         ec="none", transform=fig.transFigure))  # fmt: skip
            valores = [f"{k + 1}", f"{brecha[X]:,.0f} m", f"{brecha[Y]:,.0f} m",
                       f"{brecha[ANGULO]:.0f}°", f"{brecha[LONGITUD]:,.0f} m"]  # fmt: skip
            for valor, dx in zip(valores, anchos, strict=True):
                texto(fig, x + dx, yy, valor, 19, T, fontweight="bold" if activo else "normal")

    def cromosoma(fig, _):
        ax = eje_mapa(fig, sistema, 0.04, 0.14, 0.72)
        trazo_brechas(ax, brechas_mejor, estilo.COLOR_BRECHA)
        texto(fig, 0.50, 0.82, "Un individuo = un plan de 8 brechas", 28, T, fontweight="bold")
        tabla_genes(fig, 0.50, 0.73, None)

    def genes_uno_a_uno(fig, avance):
        k = int(round(avance * 7))
        ax = eje_mapa(fig, sistema, 0.04, 0.14, 0.72)
        trazo_brechas(ax, brechas_mejor[: k + 1], [estilo.COLOR_BRECHA] * k + [AZUL])
        texto(fig, 0.50, 0.82, "8 brechas × 4 genes = 32 números", 28, T, fontweight="bold")
        tabla_genes(fig, 0.50, 0.73, k, k + 1)

    def trazado(fig, _):
        unico = TrazadorBrechas(mapa, ConfigBrechas(k=1, longitud_max_m=3000.0))
        gen = np.array([[2950.0, 2750.0, 33.0, 1500.0]])
        mascara = unico.trazar(gen).mascaras[0]
        f0, f1, c0, c1 = 25, 38, 27, 45
        ax = fig.add_axes((0.04, 0.16, 0.50, 0.66))
        ax.imshow(np.where(mascara, 1.0, 0.0)[f0:f1, c0:c1], cmap=ListedColormap(["#cfe0b4", T]),
                  extent=(c0, c1, f1, f0), interpolation="nearest")  # fmt: skip
        for f in range(f0, f1 + 1):
            ax.axhline(f, color="white", lw=1)
        for c in range(c0, c1 + 1):
            ax.axvline(c, color="white", lw=1)
        angulo = np.radians(gen[0, ANGULO])
        x0, y0 = gen[0, X] / 100.0, gen[0, Y] / 100.0
        ax.plot([x0, x0 + np.cos(angulo) * 15], [y0, y0 + np.sin(angulo) * 15], color=NARANJA,
                lw=4)  # fmt: skip
        ax.set_axis_off()
        texto(fig, 0.58, 0.72, "Del segmento a las celdas", 30, T, fontweight="bold")
        lista(fig, 0.58, 0.60, ["Línea naranja: la brecha del cromosoma",
                                "Celdas negras: quedan sin combustible",
                                "Las esquinas se rellenan para que\n   el fuego no cruce en "
                                "diagonal",
                                "No se traza sobre agua ni poblados"], tam=20, paso=0.09)  # fmt: skip

    excedido = next(
        p for p in np.random.default_rng(11).uniform(*trazador.limites(), size=(50, 32))
        if trazador.trazar(p[None]).costos[0] > 1.5 * presupuesto
    )[None]  # fmt: skip
    reparado = trazador.reparar(excedido)

    def reparacion(fig, _):
        for x, plan, titulo, color in ((0.04, excedido, "Antes", estilo.COLOR_LLAMAS),
                                       (0.38, reparado, "Después de reparar", "#008300")):  # fmt: skip
            ax = eje_mapa(fig, sistema, x, 0.24, 0.56)
            trazo_brechas(ax, trazador.brechas(plan)[0], estilo.COLOR_BRECHA)
            costo = trazador.trazar(plan).costos[0]
            texto(fig, x + 0.158, 0.845, titulo, 22, T, ha="center", fontweight="bold")
            texto(fig, x + 0.158, 0.19, f"${costo:,.0f}", 30, color, ha="center",
                  fontweight="bold")  # fmt: skip
        texto(fig, 0.73, 0.68, "Presupuesto", 22, S)
        texto(fig, 0.73, 0.60, f"${presupuesto:,.0f}", 40, T, fontweight="bold")
        texto(fig, 0.73, 0.45, "Todas las brechas se acortan\nen la misma proporción", 20, S,
              linespacing=1.4)  # fmt: skip

    el_plan = Escena("04-plan", "El plan: un cromosoma de 32 números", [
        Tiempo("Ahora, el algoritmo genético. Cada individuo es un plan de ocho brechas. Y cada "
               "brecha se describe con cuatro números: dónde empieza, en equis y en ye, hacia "
               "dónde apunta, y cuánto mide.", cromosoma),
        Tiempo("Cuatro números por ocho brechas dan un cromosoma de treinta y dos genes. Eso es "
               "todo lo que el algoritmo manipula.", genes_uno_a_uno, cuadros=8),
        Tiempo("Para probar el plan, cada brecha se dibuja sobre la cuadrícula y sus celdas se "
               "quedan sin combustible. Las diagonales se rellenan en las esquinas, para que el "
               "fuego no se cuele entre dos celdas.", trazado),
        Tiempo("Si el plan cuesta más que el presupuesto, se repara: todas sus brechas se "
               "acortan en la misma proporción hasta que alcance el dinero.", reparacion),
    ])  # fmt: skip

    # ---- 5. La aptitud ----
    doce = simulador.tiempos_ignicion(mascara_mejor, sistema.entrenamiento)[:12]
    objetivos_mejor = corrida.frente_objetivos[indice_mejor]

    def muchos_incendios(fig, avance):
        visibles = 1 + int(round(avance * 11))
        for i in range(visibles):
            fila, col = divmod(i, 4)
            ax = eje_mapa(fig, sistema, 0.04 + col * 0.125, 0.60 - fila * 0.225, 0.21, alfa=0.7)
            trazo_brechas(ax, brechas_mejor, estilo.COLOR_BRECHA, grosor=1.4)
            capa_fuego(ax, sistema, doce[i], 10_000)
        n = len(sistema.entrenamiento)
        texto(fig, 0.58, 0.72, "Un plan, muchos incendios", 30, T, fontweight="bold")
        texto(fig, 0.58, 0.58, f"{n}", 90, AZUL, fontweight="bold")
        texto(fig, 0.58, 0.45, "escenarios por evaluación", 22, S)
        lista(fig, 0.58, 0.33, ["Cada uno con su inicio y su viento",
                                "Los mismos para todos los planes"], tam=20)  # fmt: skip

    def cuatro_objetivos(fig, _):
        area, valor, costo, impacto = objetivos_mejor
        datos = [(f"{area:,.0f} ha", "Área quemada\npromedio de los incendios", AZUL),
                 (f"{valor:,.0f}", "Valor afectado\nhectáreas × peso de la zona", AZUL),
                 (f"${costo:,.0f}", "Costo de las brechas\nmetros × costo por metro", NARANJA),
                 (f"{impacto:.1f} ha", "Impacto ecológico\nvegetación valiosa desmontada",
                  NARANJA)]  # fmt: skip
        for i, (valor_txt, pie, color) in enumerate(datos):
            tarjeta(fig, 0.04 + (i % 2) * 0.47, 0.50 - (i // 2) * 0.31, 0.45, valor_txt, pie,
                    color, tam=46)  # fmt: skip
        texto(fig, 0.04, 0.83, "Cuatro calificaciones · todas se minimizan", 26, T,
              fontweight="bold")  # fmt: skip

    def conflicto(fig, _):
        ax = eje_dispersion(fig, (0.09, 0.22, 0.46, 0.58), "Área quemada (ha)",
                            "Costo (miles de pesos)")  # fmt: skip
        frente = corrida.frente_objetivos
        ax.scatter(frente[:, AREA], frente[:, COSTO] / 1000, s=70, color=AZUL, linewidths=0)
        flecha = {"arrowstyle": "->", "color": S, "lw": 1.5}
        ax.annotate("protege más,\ncuesta más", (frente[:, AREA].min(), presupuesto / 1000),
                    xytext=(0.06, 0.30), textcoords="axes fraction", fontsize=18, color=T,
                    arrowprops=flecha)  # fmt: skip
        ax.annotate("casi gratis,\nprotege poco", (frente[:, AREA].max(), 4),
                    xytext=(0.70, 0.66), textcoords="axes fraction", fontsize=18, color=T,
                    arrowprops=flecha)  # fmt: skip
        texto(fig, 0.62, 0.66, "Los objetivos se\npelean entre sí", 32, T, fontweight="bold",
              linespacing=1.3)  # fmt: skip
        texto(fig, 0.62, 0.46, "No hay un único plan ganador:\nhay un conjunto de buenos\n"
              "compromisos.", 22, S, linespacing=1.4)  # fmt: skip

    la_aptitud = Escena("05-aptitud", "La aptitud: cómo se califica un plan", [
        Tiempo("¿Cómo se sabe si un plan es bueno? Se prueba contra trescientos incendios "
               "distintos, cada uno con su punto de inicio y su viento, y se promedian los "
               "resultados.", muchos_incendios, cuadros=12),
        Tiempo("De ahí salen cuatro calificaciones, y las cuatro se quieren lo más bajas "
               "posible: las hectáreas quemadas, el daño a las zonas de valor, el costo de las "
               "brechas, y el impacto ecológico de abrirlas.", cuatro_objetivos),
        Tiempo("Estas metas se pelean entre sí. Más brechas protegen más, pero cuestan más y "
               "desmontan más bosque. Por eso no existe un único plan ganador.", conflicto),
    ])  # fmt: skip

    # ---- 6. Pareto ----
    dos = historia[0][:, [AREA, COSTO]] / np.array([1.0, 1000.0])
    rangos = ordenamiento_no_dominado(dos)
    domina = matriz_dominancia(dos)
    candidatos = np.flatnonzero(rangos == 1)
    punto_a = int(candidatos[np.argmax(domina[candidatos].sum(axis=1))])
    dominados = np.flatnonzero(domina[punto_a])
    punto_b = int(dominados[np.argmax(np.linalg.norm(dos[dominados] - dos[punto_a], axis=1))])
    NOTA = "Población inicial · se dibujan 2 de los 4 objetivos"

    def nube(fig, colores, tamanos=60):
        ax = eje_dispersion(fig, (0.08, 0.22, 0.50, 0.58), "Área quemada (ha)",
                            "Costo (miles de pesos)")  # fmt: skip
        ax.scatter(dos[:, 0], dos[:, 1], s=tamanos, c=colores, linewidths=0, zorder=3)
        texto(fig, 0.08, 0.835, NOTA, 16, estilo.TINTA_TENUE)
        ax.text(0.03, 0.05, "↙ mejor", transform=ax.transAxes, fontsize=17, color=S)
        return ax

    def dominancia(fig, _):
        ax = nube(fig, G)
        xmax, ymax = ax.get_xlim()[1], ax.get_ylim()[1]
        ax.add_patch(Rectangle(dos[punto_a], xmax - dos[punto_a, 0], ymax - dos[punto_a, 1],
                               fc="#2a78d61f", ec="none", zorder=1))  # fmt: skip
        ax.scatter(*dos[punto_a], s=260, color=AZUL, zorder=5, edgecolors="white", linewidths=2)
        ax.scatter(*dos[punto_b], s=260, color=NARANJA, zorder=5, edgecolors="white", linewidths=2)
        ax.annotate("A", dos[punto_a], xytext=(-26, -8), textcoords="offset points", fontsize=24,
                    fontweight="bold", color=AZUL)  # fmt: skip
        ax.annotate("B", dos[punto_b], xytext=(12, -8), textcoords="offset points", fontsize=24,
                    fontweight="bold", color=NARANJA)  # fmt: skip
        texto(fig, 0.63, 0.70, "Dominancia", 32, T, fontweight="bold")
        texto(fig, 0.63, 0.55, "A domina a B:\nquema menos y cuesta menos.", 22, S,
              linespacing=1.4)  # fmt: skip
        texto(fig, 0.63, 0.39, "La zona azul es todo lo\nque A domina.", 22, S, linespacing=1.4)

    def frentes(fig, _):
        paleta = np.array([AZUL, NARANJA, AQUA, G])
        ax = nube(fig, paleta[np.minimum(rangos, 3)])
        for r, color in enumerate((AZUL, NARANJA, AQUA)):
            puntos = dos[rangos == r]
            puntos = puntos[np.argsort(puntos[:, 0])]
            ax.plot(puntos[:, 0], puntos[:, 1], color=color, lw=2, zorder=2)
        texto(fig, 0.63, 0.72, "Frentes de Pareto", 32, T, fontweight="bold")
        for i, (nombre, color) in enumerate((("Frente 1 · nadie los domina", AZUL),
                                             ("Frente 2", NARANJA), ("Frente 3", AQUA),
                                             ("Los demás", G))):  # fmt: skip
            fig.add_artist(Rectangle((0.63, 0.585 - i * 0.075), 0.02, 0.035, fc=color,
                                     transform=fig.transFigure))  # fmt: skip
            texto(fig, 0.66, 0.60 - i * 0.075, nombre, 21, S)
        texto(fig, 0.63, 0.27, "El número de frente es\nel rango del plan.", 22, T,
              linespacing=1.4)  # fmt: skip

    def apinamiento(fig, _):
        primero = rangos == 0
        distancia = distancia_apinamiento(dos, rangos)
        finita = np.where(np.isinf(distancia), np.nanmax(distancia[np.isfinite(distancia)]),
                          distancia)  # fmt: skip
        tamanos = np.where(primero, 60 + 900 * finita / finita[primero].max(), 30)
        nube(fig, np.where(primero, AZUL, "#d9d7d0"), tamanos)
        texto(fig, 0.63, 0.72, "Apiñamiento", 32, T, fontweight="bold")
        texto(fig, 0.63, 0.56, "Círculo grande = plan aislado,\nsin vecinos cerca en su frente.",
              22, S, linespacing=1.4)  # fmt: skip
        texto(fig, 0.63, 0.38, "A igual rango, se prefiere\nal más aislado: así el frente\n"
              "se mantiene repartido.", 22, T, linespacing=1.4)  # fmt: skip

    pareto = Escena("06-pareto", "Pareto: comparar sin mezclar objetivos", [
        Tiempo("Para comparar planes, Kanan usa la idea de dominancia. Un plan domina a otro si "
               "es igual o mejor en todo, y estrictamente mejor en algo.", dominancia),
        Tiempo("Los planes que nadie domina forman el primer frente de Pareto. Si se quitan, los "
               "siguientes forman el segundo frente, y así sucesivamente. Ese número de frente "
               "es el rango de cada plan.", frentes),
        Tiempo("Entre planes del mismo frente, se prefiere al que tiene menos vecinos cerca. Eso "
               "se llama distancia de apiñamiento, y sirve para que las soluciones no se "
               "amontonen en un solo lugar.", apinamiento),
    ])  # fmt: skip

    # ---- 7. El ciclo ----
    PASOS = ["Selección por torneo", "Cruza", "Mutación", "Reparación y evaluación", "Elitismo"]
    rng = np.random.default_rng(4)
    padre_a = trazador.brechas(corrida.frente_planes[indice_mejor])[0]
    padre_b = trazador.brechas(corrida.frente_planes[corrida.elegidos[EQUILIBRADO]])[0]
    de_b = rng.random(8) < 0.5
    hijo = np.where(de_b[:, None], padre_b, padre_a)
    colores_hijo = [NARANJA if b else AZUL for b in de_b]
    centro = np.array([mapa.ancho_m, mapa.alto_m]) / 2.0
    mutada = int(np.argmin(np.linalg.norm(hijo[:, :2] - centro, axis=1)))
    hijo_mutado = hijo.copy()
    hijo_mutado[mutada] += np.array([500.0, -900.0, 50.0, 0.0])

    def pasos(fig, activo: int):
        for i, nombre in enumerate(PASOS):
            y = 0.72 - i * 0.115
            es = i == activo
            fig.add_artist(FancyBboxPatch((0.04, y - 0.042), 0.27, 0.084,
                                          boxstyle="round,pad=0,rounding_size=0.01",
                                          fc=AZUL if es else "white", ec=AZUL if es else
                                          estilo.REJILLA, lw=1.5, transform=fig.transFigure))  # fmt: skip
            texto(fig, 0.058, y, f"{i + 1}.  {nombre}", 20, "white" if es else S,
                  fontweight="bold" if es else "normal")  # fmt: skip
        texto(fig, 0.175, 0.185, "↻  se repite cada generación", 17, estilo.TINTA_TENUE,
              ha="center")  # fmt: skip

    def mapa_chico(fig, x, titulo, brechas, colores, fantasma=None, alto=0.34):
        ax = eje_mapa(fig, sistema, x, 0.27, alto, alfa=0.6)
        if fantasma is not None:
            trazo_brechas(ax, fantasma, G, alfa=0.9)
        trazo_brechas(ax, brechas, colores, grosor=2.6)
        texto(fig, x + alto * RELACION / 2, 0.31 + alto, titulo, 21, T, ha="center",
              fontweight="bold")  # fmt: skip

    def torneo(fig, _):
        pasos(fig, 0)
        tarjeta(fig, 0.38, 0.46, 0.25, "Plan A", "rango 2", G, tam=40)
        tarjeta(fig, 0.69, 0.46, 0.25, "Plan B  ✓", "rango 1 · gana", AZUL, tam=40)
        texto(fig, 0.66, 0.59, "vs", 24, S, ha="center")
        texto(fig, 0.38, 0.34, "Dos planes al azar; pasa el de mejor rango.\nSi empatan, el más "
              "aislado.", 21, S, linespacing=1.4)  # fmt: skip

    def cruza(fig, _):
        pasos(fig, 1)
        mapa_chico(fig, 0.355, "Padre A", padre_a, AZUL)
        mapa_chico(fig, 0.562, "Padre B", padre_b, NARANJA)
        mapa_chico(fig, 0.769, "Hijo", hijo, colores_hijo)
        texto(fig, 0.655, 0.21, "Brechas completas de cada padre; después SBX mezcla sus números",
              18, S, ha="center")  # fmt: skip

    def mutacion(fig, _):
        pasos(fig, 2)
        mapa_chico(fig, 0.38, "Hijo", hijo, colores_hijo, alto=0.44)
        mapa_chico(fig, 0.67, "Hijo mutado", hijo_mutado,
                   [AQUA if k == mutada else c for k, c in enumerate(colores_hijo)],
                   fantasma=hijo[mutada : mutada + 1], alto=0.44)  # fmt: skip
        texto(fig, 0.655, 0.21, "Una brecha se desplaza, gira y cambia de longitud", 18, S,
              ha="center")  # fmt: skip

    def reparar_evaluar(fig, _):
        pasos(fig, 3)
        tarjeta(fig, 0.38, 0.46, 0.25, "≤ $350 mil", "se acorta si excede\nel presupuesto", T,
                tam=38)  # fmt: skip
        tarjeta(fig, 0.69, 0.46, 0.25, "300", "incendios, los mismos\npara todos", AZUL, tam=46)
        texto(fig, 0.38, 0.36, "Cada hijo recibe sus cuatro calificaciones.", 21, S)

    def elitismo(fig, _):
        pasos(fig, 4)
        ax = fig.add_axes((0.38, 0.30, 0.56, 0.42))
        ax.barh([1, 1], [100, 100], left=[0, 102], color=[AZUL, NARANJA], height=0.55)
        ax.barh([0], [100], color="#008300", height=0.55)
        ax.text(50, 1, "100 padres", ha="center", va="center", color="white", fontsize=20,
                fontweight="bold")  # fmt: skip
        ax.text(152, 1, "100 hijos", ha="center", va="center", color="white", fontsize=20,
                fontweight="bold")  # fmt: skip
        ax.text(50, 0, "100 mejores", ha="center", va="center", color="white", fontsize=20,
                fontweight="bold")  # fmt: skip
        ax.text(110, 0, "por rango y, en el último frente,\npor apiñamiento", va="center",
                fontsize=18, color=S)  # fmt: skip
        ax.set_xlim(0, 204)
        ax.set_ylim(-0.6, 1.6)
        ax.set_axis_off()

    el_ciclo = Escena("07-ciclo", "El ciclo de NSGA-II", [
        Tiempo("Con rango y apiñamiento ya se puede evolucionar. Primero, la selección: se "
               "toman dos planes al azar y gana el de mejor rango. Si empatan, gana el más "
               "aislado.", torneo),
        Tiempo("Después, la cruza. El hijo hereda brechas completas de cada padre, y luego sus "
               "números se mezclan un poco con los del otro.", cruza),
        Tiempo("Luego, la mutación: de vez en cuando una brecha se desplaza, gira, se alarga o "
               "se acorta.", mutacion),
        Tiempo("El hijo se repara si excede el presupuesto, y se califica con los mismos "
               "trescientos incendios.", reparar_evaluar),
        Tiempo("Al final, padres e hijos compiten juntos: de doscientos planes sobreviven los "
               "cien mejores. Así nunca se pierde una buena solución.", elitismo),
    ])  # fmt: skip

    # ---- 8. La evolución ----
    generaciones = len(historia) - 1
    limite_x = (historia[-1][:, AREA].min() * 0.92, historia[0][:, AREA].max() * 1.03)

    def evolucion(fig, avance):
        g = int(round(avance * generaciones))
        ax = eje_dispersion(fig, (0.075, 0.22, 0.40, 0.58), "Área quemada (ha)",
                            "Costo (miles de pesos)")  # fmt: skip
        ax.scatter(historia[0][:, AREA], historia[0][:, COSTO] / 1000, s=26, color="#d9d7d0",
                   linewidths=0, label="Generación 0")  # fmt: skip
        ax.scatter(historia[g][:, AREA], historia[g][:, COSTO] / 1000, s=52, color=AZUL,
                   linewidths=0, label="Población actual")  # fmt: skip
        ax.set_xlim(*limite_x)
        ax.set_ylim(-10, presupuesto / 1000 * 1.06)
        ax.legend(loc="lower left", fontsize=15)
        mejor = historia[g][:, AREA].min()
        texto(fig, 0.075, 0.845, f"Generación {g}", 30, T, fontweight="bold")
        texto(fig, 0.475, 0.845, f"mejor: {mejor:,.0f} ha", 24, AZUL, ha="right")
        ax_mapa = eje_mapa(fig, sistema, 0.56, 0.16, 0.66)
        plan = corrida.mejor_plan_por_generacion[g : g + 1]
        trazo_brechas(ax_mapa, trazador.brechas(plan)[0], estilo.COLOR_BRECHA)
        texto(fig, 0.745, 0.845, "Plan de menor área quemada", 20, S, ha="center")

    la_evolucion = Escena("08-evolucion", "La evolución", [
        Tiempo("Este ciclo se repite doscientas generaciones. Cada punto es un plan: hacia la "
               "izquierda quema menos, hacia abajo cuesta menos. A la derecha se ve el mejor "
               "plan de cada generación. Al principio las brechas están regadas al azar. Poco "
               "a poco se acomodan y empiezan a cerrarle el paso al fuego. En total se evalúan "
               "veinte mil planes, con seis millones de incendios simulados, en menos de medio "
               "minuto.", evolucion, cuadros=generaciones // 2 + 1),
    ])  # fmt: skip

    # ---- 9. La validación ----
    MEDIDO = {30: (545, 1165, 1261), 100: (620, 860, 1279), 300: (808, 944, 1446)}
    """Escenarios → (ha en entrenamiento, ha en prueba, ha sin brechas); ver ADR 008."""

    def sobreajuste(fig, resaltar: int | None):
        ax = fig.add_axes((0.08, 0.24, 0.50, 0.54))
        for i, (n, (entrenamiento, prueba, sin)) in enumerate(MEDIDO.items()):
            alfa = 1.0 if resaltar in (None, n) else 0.3
            barras = ax.bar([i - 0.2, i + 0.2], [entrenamiento / sin, prueba / sin], width=0.36,
                            color=[G, AZUL], alpha=alfa)  # fmt: skip
            ax.bar_label(barras, labels=[f"{entrenamiento / sin:.0%}", f"{prueba / sin:.0%}"],
                         fontsize=17, color=S, padding=4, alpha=alfa)  # fmt: skip
        ax.axhline(1.0, color=T, lw=1.5, ls="--")
        ax.text(2.45, 1.02, "sin brechas", ha="right", fontsize=15, color=S)
        ax.set_xticks(range(3), [f"{n} escenarios" for n in MEDIDO], fontsize=18)
        ax.tick_params(axis="x", labelcolor=T)
        ax.set_yticks([])
        ax.set_ylim(0, 1.15)
        ax.grid(False)
        ax.spines["left"].set_visible(False)
        texto(fig, 0.08, 0.835, "Área quemada con el mejor plan, respecto a no hacer nada", 21,
              T, fontweight="bold")  # fmt: skip
        for i, (nombre, color) in enumerate((("En los incendios con que entrenó", G),
                                             ("En incendios nuevos", AZUL))):  # fmt: skip
            fig.add_artist(Rectangle((0.63, 0.635 - i * 0.075), 0.02, 0.035, fc=color,
                                     transform=fig.transFigure))  # fmt: skip
            texto(fig, 0.66, 0.65 - i * 0.075, nombre, 20, S)

    def trampa(fig, _):
        sobreajuste(fig, 30)
        texto(fig, 0.63, 0.42, "Con 30 escenarios el plan\nse aprende esos incendios:\ncasi no "
              "protege de los nuevos.", 21, T, linespacing=1.4)  # fmt: skip

    def solucion(fig, _):
        sobreajuste(fig, 300)
        texto(fig, 0.63, 0.42, "Con 300 de entrenamiento\ny 500 de prueba aparte,\nla mejora es "
              "real.", 21, T, linespacing=1.4)  # fmt: skip

    orden = list(metodos)

    def comparacion(fig, avance):
        visibles = 1 + int(round(avance * (len(orden) - 1)))
        ax = fig.add_axes((0.30, 0.20, 0.60, 0.60))
        nombres = orden[:visibles]
        areas = [metodos[n][0] for n in nombres]
        planes = iter(estilo.COLORES_PLANES)
        colores = [next(planes) if metodos[n][2] else G for n in nombres]
        barras = ax.barh(nombres, areas, color=colores, height=0.62)
        etiquetas = [f"{a:,.0f} ha" + (f"  (−{1 - a / sin_brechas:.0%})" if a < sin_brechas else
                                       "") for a in areas]  # fmt: skip
        ax.bar_label(barras, labels=etiquetas, padding=6, fontsize=18, color=S)
        ax.set_ylim(len(orden) - 0.4, -0.6)
        ax.set_xlim(0, sin_brechas * 1.3)
        ax.set_xticks([])
        ax.grid(False)
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="y", labelsize=19, labelcolor=T, length=0)
        texto(fig, 0.04, 0.845, "Área quemada media en 500 incendios nuevos · mismo presupuesto",
              22, T, fontweight="bold")  # fmt: skip

    la_validacion = Escena("09-validacion", "La validación: ¿de verdad funciona?", [
        Tiempo("Hay una trampa. Si el algoritmo siempre ve los mismos incendios, puede "
               "aprenderse esos incendios en vez de aprender a proteger el bosque. Con solo "
               "treinta escenarios, eso fue justo lo que pasó.", trampa),
        Tiempo("Por eso Kanan entrena con trescientos escenarios, y se califica al final con "
               "quinientos incendios nuevos que nunca vio.", solucion),
        Tiempo("Y se compara, con el mismo presupuesto, contra métodos simples: no hacer nada, "
               "poner brechas al azar, rodear los poblados, y una búsqueda aleatoria con el "
               "mismo esfuerzo de cómputo. El mejor plan de Kanan reduce el área quemada en "
               "treinta y cinco por ciento. Las brechas al azar, apenas ocho.", comparacion,
               cuadros=len(orden)),
    ])  # fmt: skip

    # ---- 10. El resultado ----
    def tres_planes(fig, _):
        for i, clave in enumerate((MENOR_AREA, EQUILIBRADO, MENOR_COSTO)):
            x = 0.055 + i * 0.31
            color = estilo.COLORES_PLANES[list(corrida.elegidos).index(clave)]
            indice = corrida.elegidos[clave]
            ax = eje_mapa(fig, sistema, x, 0.30, 0.47, alfa=0.75)
            trazo_brechas(ax, trazador.brechas(corrida.frente_planes[indice])[0], color)
            area, costo, _ = metodos[f"Kanan · {NOMBRES[clave].lower()}"]
            texto(fig, x + 0.132, 0.815, NOMBRES[clave], 22, color, ha="center",
                  fontweight="bold")  # fmt: skip
            texto(fig, x + 0.132, 0.245, f"−{1 - area / sin_brechas:.0%} de área quemada", 22, T,
                  ha="center", fontweight="bold")  # fmt: skip
            texto(fig, x + 0.132, 0.19, f"${costo:,.0f}", 20, S, ha="center")

    def limites(fig, _):
        texto(fig, 0.5, 0.78, "Es un prototipo de apoyo a la decisión", 32, T, ha="center",
              fontweight="bold")  # fmt: skip
        lista(fig, 0.22, 0.63, ["El mapa es sintético, no La Sepultura real",
                                "Los costos y los valores ecológicos son supuestos",
                                "El modelo de fuego es una simplificación",
                                "La decisión final es de las personas"], tam=24, paso=0.10)  # fmt: skip

    def cierre(fig, _):
        etapas = ["Mapa", "Plan de\n8 brechas", "Incendios\nsimulados", "4 objetivos", "NSGA-II",
                  "Frente de\nPareto"]  # fmt: skip
        for i, etapa in enumerate(etapas):
            x = 0.045 + i * 0.155
            fig.add_artist(FancyBboxPatch((x, 0.56), 0.13, 0.15, fc="white", ec=AZUL, lw=2,
                                          boxstyle="round,pad=0,rounding_size=0.012",
                                          transform=fig.transFigure))  # fmt: skip
            texto(fig, x + 0.065, 0.635, etapa, 20, T, ha="center", linespacing=1.3)
            if i < len(etapas) - 1:
                texto(fig, x + 0.1425, 0.635, "→", 26, AZUL, ha="center")
        texto(fig, 0.5, 0.38, "Kanan", 80, T, ha="center", fontweight="bold")
        texto(fig, 0.5, 0.26, "Un algoritmo que aprende a proteger el bosque", 26, AZUL,
              ha="center")  # fmt: skip

    el_resultado = Escena("10-resultado", "El resultado", [
        Tiempo("Kanan no entrega una sola respuesta, sino un frente de planes. De ahí se "
               "muestran tres: el que menos deja arder, uno equilibrado, y el más barato que "
               "todavía protege.", tres_planes),
        Tiempo("Y hay que decirlo claro: es un prototipo. El mapa es sintético, los costos son "
               "supuestos, y el modelo de fuego es una simplificación. Sirve para apoyar una "
               "decisión, no para sustituirla.", limites),
        Tiempo("En resumen: un mapa, planes de ocho brechas, cientos de incendios simulados, "
               "cuatro objetivos, y un algoritmo genético que conserva lo mejor de cada "
               "generación. Eso es Kanan.", cierre),
    ])  # fmt: skip

    return [problema, el_mapa, el_fuego, el_plan, la_aptitud, pareto, el_ciclo, la_evolucion,
            la_validacion, el_resultado]  # fmt: skip
