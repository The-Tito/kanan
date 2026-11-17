# Plan 01 · Base de conocimiento y mapa sintético

Rama: `feature/base-conocimiento` · Paso 1 del brief (parte de mapas)

## Qué se construye

- `dominio/catalogos.py`: vegetación (`p_veg`, valor ecológico, costo de desmonte por metro),
  densidad (`p_den`, factores) y zonas de valor (pesos).
- `dominio/mapa.py`: `Mapa`, capas por celda (vegetación, densidad, elevación, zona de valor,
  caminos, probabilidad de ignición) y propiedades derivadas (combustible, construible,
  pendiente).
- `dominio/mapa_sintetico.py`: generador reproducible por semilla.

## Cómo

1. Relieve: rampa hacia el noreste más dos octavas de ruido suave.
2. Vegetación por altitud y humedad; densidad por ruido independiente.
3. Río 4-conexo que baja por la pendiente (barrera natural completa).
4. Tres poblados en la parte baja, con cultivos alrededor y caminos que los unen.
5. Zona núcleo en la parte alta; infraestructura a mitad de los caminos.
6. Probabilidad de ignición que decae con la distancia a caminos y cultivos.

## Pruebas

- Misma semilla, mismo mapa.
- El mapa contiene todos los rasgos (agua, poblados, zonas de valor, caminos).
- No se puede construir sobre agua ni poblados; la ignición suma 1 y es mayor cerca de caminos.
