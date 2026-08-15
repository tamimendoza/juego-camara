## 1. Nubes en movimiento (engine Mario)

- [x] 1.1 Agregar parámetro `draw_clouds: bool = True` a `_render_static_environment` en `src/mario_game.py`; con `False` omitir el loop de nubes estáticas y dibujar solo arbustos, flores, suelo y graffiti.
- [x] 1.2 En `_render_game` de `src/mario_game.py`, llamar `_render_static_environment(frame, draw_clouds=False)` (las nubes visibles pasan a ser solo la capa en movimiento).
- [x] 1.3 Agregar método `_seed_clouds(current_speed)` en `src/mario_game.py` que cree 4-5 nubes con `x` repartido entre ~15% y ~95% del ancho, `y` en `[40, ground_y//2]` y tamaño de `CLOUD_SIZE_RANGE`.
- [x] 1.4 En `reset()` de `src/mario_game.py`, reemplazar `self._clouds = []` por la capa sembrada (`_seed_clouds(self.speed)`) para que el cielo arranque poblado.
- [x] 1.5 En `src/mario_face_game.py`, en `_render_game` llamar `_render_static_environment(frame, draw_clouds=False)`; `_render_menu` conserva las nubes estáticas de fondo.

## 2. Detección de rostro de lejos

- [x] 2.1 En `src/mario_face_main.py`, configurar `FaceLandmarkerDetector` con `min_face_detection_confidence=0.3`, `min_tracking_confidence=0.3` y agregar `min_face_presence_confidence=0.3`.

## 3. Tests y verificación

- [x] 3.1 En `tests/test_mario_game.py`, agregar tests: tras `engine.start()`, `_clouds` no está vacía y todas las nubes reducen su `x` tras `_update_clouds`; y `_render_static_environment(frame, draw_clouds=False)` no dibuja píxeles de nube (blancos) arriba del cielo.
- [x] 3.2 Ejecutar la suite completa: `python3 -m pytest tests/ -q`.
- [ ] 3.3 Verificación manual con `./run_mario_face.sh`: cielo poblado de nubes todas en movimiento durante el juego, y el rostro se detecta a mayor distancia de la cámara.
