## Context

`MarioFaceGameEngine` (src/mario_face_game.py) extiende `MarioGameEngine` (src/mario_game.py)
y es el único juego lanzado por `run_mario_face.sh`. Estado actual relevante:

- El graffiti "Familia Mendoza Silva" se dibuja en `_render_static_environment`
  (src/mario_game.py:869) en `(width//2 - 100, ground_top - 10)`, es decir, encima del
  suelo, en el cielo. `MarioFaceGameEngine._render_game` llama a
  `self._render_static_environment(frame, draw_clouds=False)`.
- Las nubes con sprite (`sprites/cloud_sprite.png`, 145x35 px, proporción ~4.1:1) se
  redimensionan a `(width, height)` con `height = width * 2 // 3` en
  `MarioFaceGameEngine._spawn_cloud` / `_seed_clouds` (src/mario_face_game.py:305-337),
  resultando casi cuadradas y con aspecto de llama.
- `FaceCropper.overlay_face` (src/face_crop.py:140) ya mezcla `face_image` + `face_mask`
  sobre un frame en un `center`/`radius` dados; se reutiliza para la vista previa.
- El alcance aprobado es solo la variante Mario Face Jump.

## Goals / Non-Goals

**Goals:**
- Mover el graffiti a los ladrillos (debajo de `ground_y`) solo en el Mario Face Jump.
- Recortar la altura de las nubes con sprite para que conserven proporción de nube.
- Mostrar una vista previa circular del rostro en vivo abajo a la derecha, sobre los
  ladrillos, sin interferir con el juego.

**Non-Goals:**
- No cambiar el Mario Bros estándar (`mario_main`), `minecraft_game.py` ni `game.py`.
- No tocar detección, salto, vidas, música, monedas, niveles ni obstáculos.
- No cambiar el sprite de nube (se recorta solo la altura de renderizado).

## Decisions

**D1. Posición del graffiti vía parámetro opcional en `_render_static_environment`.**
Se agrega `graffiti_y: Optional[int] = None` a `_render_static_environment`
(src/mario_game.py). Si es `None` se mantiene el comportamiento actual
(`ground_top - 10`); si viene un valor se usa como línea base `cv2.putText`. El
`MarioFaceGameEngine` define `GRAFFITI_BRICK_Y_OFFSET = 15` y pasa
`graffiti_y=self._ground_y + GRAFFITI_BRICK_Y_OFFSET` en sus llamadas (juego y menú),
dejando el texto sobre los ladrillos. Es un cambio no destructivo: el Mario Bros
estándar no pasa el parámetro y conserva su apariencia.
- Alternativa descartada: sobrescribir `_render_static_environment` por completo en
  `MarioFaceGameEngine` — duplica ~30 líneas de renderizado (arbustos, ladrillos,
  patrón) sin beneficio y se desincroniza si el padre cambia.

**D2. Altura de nube recortada con proporción del sprite.**
En `MarioFaceGameEngine._spawn_cloud` y `_seed_clouds`, reemplazar
`height = width * 2 // 3` por `height = max(width // 4, 8)`, que se aproxima a la
proporción del sprite 145x35 (~4:1) y evita el aspecto de llama. Se deja un mínimo de 8px
para que nubes de tamaño mínimo sigan visibles.
- Alternativa descartada: usar `int(width * 0.24)` exacto del sprite — equivalente
  visual a `width // 4`, más frágil ante cambios de sprite. `width // 4` es legible y
  suficiente.
- Nota: las nubes sin sprite (elipse) del engine base no se tocan (fuera de alcance).

**D3. Vista previa circular del rostro con `FaceCropper.overlay_face`.**
Se define `_FACE_PREVIEW_RADIUS = 25` y posición fija abajo a la derecha sobre los
ladrillos: `preview_center = (self.width - 35, self._ground_y + 30)`. En
`MarioFaceGameEngine._render_game`, después de `_draw_hud`:
- Si `self._face_image` y `self._face_mask` existen, se llama
  `FaceCropper().overlay_face(frame, self._face_image, self._face_mask, preview_center, _FACE_PREVIEW_RADIUS)`.
- Si no hay rostro, se dibuja solo el contorno del círculo (`cv2.circle`, grosor 1) para
  marcar el área objetivo.
La posición (25px de radio, esquina inferior derecha, sobre ladrillos) queda fuera de la
zona de juego (el personaje vive en x≈80 y los obstáculos cruzan el centro). Como
`_render_game_over` llama a `_render_game` antes de atenuar, la vista previa sigue
visible (atenuada) en el overlay de game over, cumpliendo el requisito.
- Alternativa descartada: integrar la vista previa al HUD superior — no resuelve
  "sobre los ladrillos" ni "no interrumpe el juego".

## Risks / Trade-offs

- [El cambio en `_render_static_environment` afecta al engine compartido] → Es aditivo
  (parámetro con default `None`); el Mario Bros estándar no lo usa y sus tests no cambian.
- [`width // 4` puede dejar nubes demasiado chatas en tamaños mínimos] → Mínimo 8px de
  altura; se mantiene la proporción ancha de nube pedida.
- [La vista previa puede tapar un ladrillo u obstáculo en la esquina] → Es un área
  pequeña y fija que no está en el recorrido del personaje; no afecta colisiones ni HUD.

## Migration Plan

1. Implementar `graffiti_y` opcional en `mario_game.py` y las tres piezas en
   `mario_face_game.py`.
2. Actualizar `tests/test_mario_face_game.py` y correr la suite
   (`python3 -m pytest tests/ -q`); verificar que `test_mario_game.py` y `test_game.py`
   siguen verdes.
3. Rollback: revertir los dos archivos no rompe otros variantes (el cambio compartido es
   aditivo).

## Open Questions

Ninguna que afecte specs, enfoque o desglose de tareas.
