## 1. Posiciones estáticas relativas a la resolución

- [ ] 1.1 En `src/games/mario/mario_game.py`, reemplazar `_BUSH_OFFSETS` y
      `_CLOUD_OFFSETS` por funciones `_bush_positions(width, ground_y)` y
      `_cloud_positions(width, ground_y)` que distribuyan las posiciones
      proporcionalmente al ancho y anclen los arbustos al suelo (`ground_y - 8`)
      y las nubes al cielo (`~0.18 × ground_y`).
- [ ] 1.2 Actualizar `_render_static_environment` para usar las funciones
      relativas en lugar de las listas fijas.

## 2. Velocidad multiplicativa en Mario Face Jump

- [ ] 2.1 En `src/games/mario/mario_face_game.py`, reemplazar `SPEED_INCREMENT = 0.1`
      por `SPEED_MULTIPLIER = 2.0`.
- [ ] 2.2 Cambiar la property `speed` de `MarioFaceGameEngine` a
      `BASE_SPEED * SPEED_MULTIPLIER ** (level - 1)`.
- [ ] 2.3 Actualizar `_draw_hud` y `_render_game_over` para mostrar el multiplicador
      multiplicativo `2.0^(nivel−1)`.

## 3. Tests

- [ ] 3.1 Actualizar `tests/games/test_mario_face_game.py`: `test_speed_progression`
      pasa a la fórmula multiplicativa (`BASE_SPEED`, `BASE_SPEED*2.0`,
      `BASE_SPEED*4.0` en niveles 1, 2, 3).
- [ ] 3.2 Añadir test en `tests/games/test_mario_face_game.py`: los arbustos
      estáticos se dibujan sobre el suelo a 720p (`_ground_y - r` ≤ y < `_ground_y`).
- [ ] 3.3 Ejecutar `python3 -m pytest tests/ -q` y confirmar que toda la suite pasa
      (incluidos `test_mario_game.py` y `test_jump_game.py`).

## 4. Verificación

- [ ] 4.1 `openspec validate` sobre el change y `openspec archive` al completar.
