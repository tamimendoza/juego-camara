## 1. Graffiti sobre los ladrillos

- [x] 1.1 En `src/mario_game.py`, agregar parámetro `graffiti_y: Optional[int] = None` a
      `_render_static_environment`; si es `None` usar `ground_top - 10` (comportamiento
      actual), si viene un valor usarlo como línea base del `cv2.putText`.
- [x] 1.2 En `src/mario_face_game.py`, definir `GRAFFITI_BRICK_Y_OFFSET = 15` y pasar
      `graffiti_y=self._ground_y + GRAFFITI_BRICK_Y_OFFSET` en la llamada a
      `_render_static_environment` de `_render_game` (y `_render_menu` si corresponde).
- [x] 1.3 Verificar que el Mario Bros estándar (`_render_static_environment` sin el
      parámetro) conserva la posición original del graffiti.

## 2. Altura de nubes recortada

- [x] 2.1 En `src/mario_face_game.py`, en `_spawn_cloud` y `_seed_clouds`, reemplazar
      `height = width * 2 // 3` por `height = max(width // 4, 8)` para conservar la
      proporción ancha del sprite y no parecer fuego.

## 3. Vista previa circular del rostro

- [x] 3.1 En `src/mario_face_game.py`, definir `_FACE_PREVIEW_RADIUS = 25` y el centro
      `preview_center = (self.width - 35, self._ground_y + 30)`.
- [x] 3.2 En `MarioFaceGameEngine._render_game`, tras `_draw_hud`, dibujar la vista
      previa: con `self._face_image`/`self._face_mask` usar
      `FaceCropper().overlay_face(frame, ..., preview_center, _FACE_PREVIEW_RADIUS)`;
      sin rostro, dibujar el contorno del círculo (`cv2.circle`, grosor 1).

## 4. Tests y verificación

- [x] 4.1 En `tests/test_mario_face_game.py`, agregar tests: `_render_static_environment`
      con `graffiti_y` dibuja el texto debajo de `ground_y`; `_spawn_cloud`/`_seed_clouds`
      producen nubes con `height < width`; `_render_game` con y sin rostro dibuja la vista
      previa sin excepción (pixel no-celeste en la esquina inferior derecha).
- [x] 4.2 Ejecutar la suite completa: `python3 -m pytest tests/ -q`, verificando que
      `test_mario_game.py` y `test_game.py` siguen verdes.
- [ ] 4.3 Verificación manual con `./run_mario_face.sh`: graffiti sobre los ladrillos,
      nubes anchas (no llamas) y círculo de rostro visible abajo a la derecha.
