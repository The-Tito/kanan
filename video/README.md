# Video explicativo

Un video de unos 7 minutos que explica cómo funciona Kanan por dentro: el mapa, el autómata
del fuego, el cromosoma, la aptitud, Pareto, el ciclo de NSGA-II, la evolución y la
validación. Todo lo que se ve se dibuja con el código y los datos reales de una corrida.

## Generarlo

Requiere `ffmpeg` instalado. Desde la raíz del repositorio:

```bash
.venv/bin/python -m video.generar
```

La primera vez ejecuta Kanan (cerca de un minuto) y guarda los datos en `video/.trabajo/`.
El resultado queda en `video/salida/kanan_explicado.mp4` (1920 × 1080, 30 cuadros por
segundo, con subtítulos).

## Ponerle narración

1. Los textos a narrar están en [`guion/`](guion), uno por escena, y completos en
   [`guion.md`](guion.md).
2. Genera un audio por escena (por ejemplo en ElevenLabs) y guárdalo en `video/audio/` con el
   mismo nombre que su texto: `01-problema.mp3`, `02-mapa.mp3`, … `10-resultado.mp3`. También
   se aceptan `.wav` y `.m4a`.
3. Vuelve a ejecutar el comando de arriba.

Cada escena toma la duración de su audio, y dentro de ella cada imagen cambia cuando empieza
su frase. Las escenas sin audio quedan en silencio con una duración estimada (2.5 palabras por
segundo), así que se puede avanzar escena por escena.

Opciones:

```bash
.venv/bin/python -m video.generar --escenas 03-fuego 08-evolucion
```

```bash
.venv/bin/python -m video.generar --sin-subtitulos
```

## Cambiar el contenido

- `escenas.py`: qué se dice y qué se dibuja en cada frase. El guion se genera de aquí; no se
  edita `guion/` a mano.
- `motor.py`: tiempos, subtítulos y codificación con ffmpeg.
- `datos.py`: la corrida de Kanan que alimenta las figuras.

Si se cambia el texto de una escena hay que volver a generar su audio.
