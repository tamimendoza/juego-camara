## Context

`MarioGameEngine` (src/mario_game.py) es un engine autónomo (no hereda de `GameEngine` en
src/game.py) y es la base de la variante Mario Face (`MarioFaceGameEngine` en
src/mario_face_game.py). Actualmente:

- La escena de juego dibuja nubes estáticas en posiciones fijas (`_CLOUD_OFFSETS` dentro de
  `_render_static_environment`) y encima una capa de nubes en movimiento (`self._clouds`).
- `reset()` deja `self._clouds = []` y `_cloud_timer = 0`, así que al arrancar la partida no
  hay ninguna nube en movimiento; recién aparece una cada 180-300 frames (~1-2 a la vez).
  El resultado visible es "solo se mueven algunas nubes".
- El FaceLandmarker se configura en `src/mario_face_main.py` con
  `min_face_detection_confidence=0.5` y `min_tracking_confidence=0.5`
  (`min_face_presence_confidence` usa el default 0.5), lo que descarta rostros pequeños/lejanos.

## Goals / Non-Goals

**Goals:**
- Que todas las nubes visibles durante el juego se desplacen de derecha a izquierda.
- Que el cielo arranque poblado de nubes en movimiento al iniciar/reiniciar la partida.
- Que el rostro se detecte también cuando el jugador está lejos de la cámara.

**Non-Goals:**
- No cambiar `game.py` (juego genérico) ni `minecraft_game.py`: el cambio de nubes se limita
  a la familia Mario (`mario_game.py` + `mario_face_game.py`), que es lo que lanza
  `run_mario_face.sh`.
- No cambiar el modelo (seguimos con `models/face_landmarker.task`), ni agregar upscaling de
  frame, ni cambiar la arquitectura de detección.
- No modificar el comportamiento de obstáculos, saltos, niveles o vidas.

## Decisions

**D1. Quitar las nubes estáticas de la escena de juego.**
`_render_static_environment` gana un parámetro `draw_clouds: bool = True`. En `_render_game`
(de `mario_game.py` y `mario_face_game.py`) se llama con `draw_clouds=False`, dejando solo
arbustos + suelo + graffiti. `_render_menu` y `_render_game_over` siguen dibujando nubes
estáticas como fondo.
- Alternativa descartada: eliminar las nubes estáticas en todos los estados (quedarían las
  pantallas de menú/game over sin cielo).
- Alternativa descartada: hacer que las nubes estáticas "arranquen" como nubes en movimiento —
  agrega complejidad de estado y sincronización sin beneficio frente a sembrar la capa móvil.

**D2. Sembrar la capa de nubes en movimiento al reiniciar.**
Se agrega `_seed_clouds(current_speed)` que crea 4-5 nubes con `x` repartido a lo ancho de la
pantalla (p.ej. entre 15% y 95% del ancho), `y` en el rango actual y tamaño de
`CLOUD_SIZE_RANGE`. Se invoca desde `reset()` (donde `self.speed` ya es `BASE_SPEED`, nivel 1),
reemplazando `self._clouds = []`. Así, al pasar a PLAYING el cielo ya tiene nubes y todas se
desplazan. `_spawn_cloud` se reutiliza/sirve de base (con un `x` opcional o replicando su
lógica en `_seed_clouds`). Se mantiene el intervalo de aparición actual (`CLOUD_SPAWN_INTERVAL`),
pues la capa ya queda poblada.
- Alternativa descartada: bajar `CLOUD_SPAWN_INTERVAL` global — cambia densidad constante de
  todos los juegos y no resuelve el arranque vacío.

**D3. Bajar umbrales del FaceLandmarker.**
En `src/mario_face_main.py`, `FaceLandmarkerDetector(..., min_face_detection_confidence=0.3,
min_tracking_confidence=0.3)` y se agrega `min_face_presence_confidence=0.3`. El resto del
pipeline (crop, overlay, fallback al Mario head) no cambia.
- Alternativa descartada: upscaling del frame antes de detectar (más caro, cambia el contrato
  del pipeline). Queda como mejora futura si 0.3 no alcanza.
- Nota: valores < 0.3 pueden aumentar falsos positivos; 0.3 es un punto medio razonable y
  ajustable en una sola línea.

**D4. Cambio en el engine base afecta a Mario y Mario Face por igual.**
`_render_game` y `reset()` viven en `MarioGameEngine`, compartido por `mario_main` y
`mario_face_main`. El comportamiento nuevo (todas las nubes en movimiento) aplica a ambas
variantes; es consistente con la especificación `game-moving-clouds` que describe el cielo del
juego Mario. La variante Face solo ajusta su propia llamada a `_render_static_environment`.

## Risks / Trade-offs

- [Umbrales bajos pueden aumentar falsos positivos de rostro] → Mitigación: 0.3 como punto
  medio; si aparece ruido, subir solo `min_face_presence_confidence`. El overlay siempre
  vuelve al fallback Mario head cuando no hay detección.
- [Afecta a la variante Mario estándar (mismo engine)] → Es el comportamiento deseado y
  consistente; no hay regresión esperada porque solo se reemplaza el fondo de nubes fijas
  por nubes móviles ya existentes.
- [El rendimiento no cambia: misma cantidad de nubes renderizadas] → El recuento de nubes
  móviles sembradas (4-5) está en el mismo orden que las 5 estáticas que se quitan.

## Migration Plan

No aplica: cambio local sin dependencias externas. Rollback trivial (revertir los cambios en
`mario_game.py`, `mario_face_game.py` y `mario_face_main.py`).

## Open Questions

Ninguna que afecte specs, enfoque o desglose de tareas.
