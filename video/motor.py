"""Motor del video: convierte escenas (texto + dibujo) en un MP4 sincronizado con la narración.

Una escena es una lista de tiempos. Cada tiempo tiene la frase que se narra y la función que
dibuja lo que se ve mientras se dice. La duración de una escena es la de su audio; si aún no
hay audio, se estima con el número de palabras. Dentro de la escena, cada tiempo dura en
proporción a sus palabras, así la imagen cambia cuando empieza su frase.
"""

from __future__ import annotations

import math
import re
import subprocess
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from kanan.salidas import estilo

ANCHO_PULGADAS, ALTO_PULGADAS, DPI = 16, 9, 120
CUADROS_POR_SEGUNDO = 30
PALABRAS_POR_SEGUNDO = 2.5
"""Ritmo estimado de la narración cuando todavía no hay audio."""
PAUSA_FINAL = 0.8
CARACTERES_SUBTITULO = 150
EXTENSIONES_AUDIO = (".mp3", ".wav", ".m4a", ".aac", ".ogg")

Dibujar = Callable[[Figure, float], None]
"""Recibe la figura y el avance del tiempo (0 a 1)."""


@dataclass(frozen=True)
class Tiempo:
    texto: str
    dibujar: Dibujar
    cuadros: int = 1
    """Más de 1 anima el dibujo a lo largo de la frase."""


@dataclass(frozen=True)
class Escena:
    clave: str
    titulo: str
    tiempos: list[Tiempo]

    def narracion(self) -> str:
        return " ".join(t.texto for t in self.tiempos)

    def palabras(self) -> int:
        return len(self.narracion().split())


@dataclass(frozen=True)
class Cuadro:
    dibujar: Dibujar
    avance: float
    subtitulo: str
    duracion: float


def buscar_audio(carpeta: Path, clave: str) -> Path | None:
    for extension in EXTENSIONES_AUDIO:
        ruta = carpeta / f"{clave}{extension}"
        if ruta.exists():
            return ruta
    return None


def duracion_audio(ruta: Path) -> float:
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(ruta)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    return float(salida.stdout.strip())


def trocear(texto: str, maximo: int = CARACTERES_SUBTITULO) -> list[str]:
    """Subtítulos de dos líneas como máximo, cortados en los puntos de la narración.

    Cada oración es un subtítulo; las que no caben se parten en trozos parejos.
    """
    trozos: list[str] = []
    for oracion in re.split(r"(?<=[.?!])\s+", texto.strip()):
        if len(oracion) <= maximo:
            trozos.append(oracion)
        else:
            partes = math.ceil(len(oracion) / maximo)
            trozos += textwrap.wrap(oracion, math.ceil(len(oracion) / partes) + 12)
    return trozos or [""]


def planear(escena: Escena, duracion: float) -> list[Cuadro]:
    """Reparte la duración entre los tiempos y sus subtítulos."""
    total = sum(len(t.texto.split()) for t in escena.tiempos)
    cuadros: list[Cuadro] = []
    for tiempo in escena.tiempos:
        d = duracion * len(tiempo.texto.split()) / total
        trozos = trocear(tiempo.texto)
        letras = sum(len(t) for t in trozos)
        cortes_sub, acumulado = [], 0.0
        for trozo in trozos:
            cortes_sub.append(acumulado)
            acumulado += d * len(trozo) / letras
        n = tiempo.cuadros
        cortes = sorted({*cortes_sub, *(d * i / n for i in range(n))})
        for i, inicio in enumerate(cortes):
            fin = cortes[i + 1] if i + 1 < len(cortes) else d
            indice = min(int(inicio / d * n + 1e-9), n - 1)
            avance = indice / (n - 1) if n > 1 else 1.0
            sub = trozos[max(j for j, c in enumerate(cortes_sub) if c <= inicio + 1e-9)]
            cuadros.append(Cuadro(tiempo.dibujar, avance, sub, fin - inicio))
    ultimo = cuadros[-1]
    cuadros[-1] = Cuadro(ultimo.dibujar, ultimo.avance, ultimo.subtitulo,
                         ultimo.duracion + PAUSA_FINAL)  # fmt: skip
    return cuadros


def _marco(figura: Figure, numero: int, total: int, titulo: str, subtitulo: str | None) -> None:
    """Encabezado de la escena, barra de avance y subtítulo."""
    figura.text(0.04, 0.935, f"{numero:02d}", fontsize=20, color=estilo.SERIE_1,
                fontweight="bold", va="center")  # fmt: skip
    figura.text(0.075, 0.935, titulo, fontsize=24, color=estilo.TINTA, fontweight="bold",
                va="center")  # fmt: skip
    figura.text(0.96, 0.935, "Kanan", fontsize=16, color=estilo.TINTA_TENUE, ha="right",
                va="center")  # fmt: skip
    figura.add_artist(plt.Line2D([0.04, 0.96], [0.895, 0.895], color=estilo.REJILLA, lw=1.5))
    figura.add_artist(plt.Line2D([0.04, 0.04 + 0.92 * numero / total], [0.895, 0.895],
                                 color=estilo.SERIE_1, lw=3))  # fmt: skip
    if subtitulo:
        figura.text(0.5, 0.062, textwrap.fill(subtitulo, 78), fontsize=19, ha="center",
                    va="center", color=estilo.TINTA, linespacing=1.35)  # fmt: skip


def renderizar_escena(
    escena: Escena, numero: int, total: int, carpeta_audio: Path, trabajo: Path,
    con_subtitulos: bool = True,
) -> tuple[Path, float, bool]:  # fmt: skip
    """Genera el MP4 de una escena. Devuelve su ruta, su duración y si llevó audio."""
    estilo.aplicar()
    plt.rcParams["font.family"] = ["Helvetica Neue", "Arial", "DejaVu Sans"]
    audio = buscar_audio(carpeta_audio, escena.clave)
    hablado = duracion_audio(audio) if audio else escena.palabras() / PALABRAS_POR_SEGUNDO
    cuadros = planear(escena, hablado)
    duracion = hablado + PAUSA_FINAL

    carpeta = trabajo / escena.clave
    carpeta.mkdir(parents=True, exist_ok=True)
    for viejo in carpeta.glob("*.png"):
        viejo.unlink()
    figura = plt.figure(figsize=(ANCHO_PULGADAS, ALTO_PULGADAS), dpi=DPI)
    lineas = []
    for i, cuadro in enumerate(cuadros):
        figura.clear()
        cuadro.dibujar(figura, cuadro.avance)
        _marco(figura, numero, total, escena.titulo, cuadro.subtitulo if con_subtitulos else None)
        ruta = carpeta / f"{i:04d}.png"
        figura.savefig(ruta, dpi=DPI)
        lineas += [f"file '{ruta.resolve()}'", f"duration {cuadro.duracion:.4f}"]
    lineas.append(f"file '{ruta.resolve()}'")
    plt.close(figura)
    lista = carpeta / "cuadros.txt"
    lista.write_text("\n".join(lineas), encoding="utf-8")

    salida = trabajo / f"{escena.clave}.mp4"
    orden = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista)]
    if audio:
        orden += ["-i", str(audio), "-af", "apad"]
    else:
        orden += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    orden += [
        "-vf", f"fps={CUADROS_POR_SEGUNDO},format=yuv420p", "-c:v", "libx264", "-crf", "18",
        "-preset", "medium", "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "160k",
        "-t", f"{duracion:.3f}", str(salida),
    ]  # fmt: skip
    subprocess.run(orden, check=True)
    return salida, duracion, audio is not None


def unir(partes: list[Path], salida: Path) -> None:
    lista = salida.with_suffix(".txt")
    lista.write_text("\n".join(f"file '{p.resolve()}'" for p in partes), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
         "-c", "copy", "-movflags", "+faststart", str(salida)],
        check=True,
    )  # fmt: skip
    lista.unlink()
