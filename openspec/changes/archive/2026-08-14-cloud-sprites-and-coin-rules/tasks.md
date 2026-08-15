## 1. Asset de sprites

- [x] 1.1 Recortar el sprite de nube de `sprites/smb1_misc_sprites.gif` (región ~x=[47,192],
      y=[199,234], preservando transparencia) y guardarlo como `sprites/cloud_sprite.png` (RGBA).
- [x] 1.2 Verificar que `sprites/cloud_sprite.png` y `sprites/SMW_v-ram-yane_QuestionMarkBlock.png`
      se cargan con `cv2.imread(..., cv2.IMREAD_UNCHANGED)` devolviendo 4 canales.

## 2. Extensiones no destructivas del engine compartido

- [x] 2.1 En `src/game.py`, añadir a `Cloud.__init__` el parámetro `sprite: Optional[np.ndarray] = None`
      y en `Cloud.render` usar el sprite (escalado a `(width, height)` con alpha blending) cuando
      esté presente; si es `None`, mantener la elipse actual.
- [x] 2.2 En `src/mario_game.py`, añadir `self._coins = 0` en `__init__` y reiniciarlo en `reset()`.
- [x] 2.3 En `src/mario_game.py` `_update_playing`, sumar `self._coins += 1` junto al
      `play_coin()` cuando un obstáculo es superado.

## 3. Overrides en MarioFaceGameEngine

- [x] 3.1 Definir en `src/mario_face_game.py` `SPEED_INCREMENT = 0.1` y sobrescribir la property
      `speed` con `BASE_SPEED * (1 + SPEED_INCREMENT * (level - 1))`.
- [x] 3.2 Sobrescribir `_render_game` para pintar el fondo con `SKY_COLOR` (celeste) en lugar de
      `(200, 230, 255)`.
- [x] 3.3 Sobrescribir `_spawn_cloud`/`_seed_clouds` para crear nubes con el sprite
      `cloud_sprite.png` (fallback a `None` si no se carga).
- [x] 3.4 Sobrescribir `_update_sky_blocks` para: al recolectar un cuadrado, sumar
      `self._coins += 1` y reproducir `play_coin` (sin sumar vida); y spawn de **un** cuadrado
      por hito de nivel (cada 5 obstáculos superados), eliminando el spawn por temporizador
      aleatorio.
- [x] 3.5 Sobrescribir `_spawn_sky_block` para dibujar el cuadrado con el sprite
      `SMW_v-ram-yane_QuestionMarkBlock.png` escalado a `SKY_BLOCK_SIZE` (fallback al rectángulo
      amarillo si el sprite no carga).
- [x] 3.6 Sobrescribir `_draw_hud` para mostrar `Monedas: {self._coins}` (acumulado) y el
      multiplicador aditivo `1 + 0.1*(level-1)`.
- [x] 3.7 Sobrescribir `_render_game_over` para mostrar el multiplicador aditivo y el total de
      monedas acumulado.

## 4. Tests

- [x] 4.1 En `tests/test_mario_face_game.py`, ajustar `test_speed_progression` a la fórmula
      aditiva (`BASE_SPEED`, `BASE_SPEED*1.1`, `BASE_SPEED*1.2` en niveles 1, 2, 3).
- [x] 4.2 Añadir test: al pasar 5 obstáculos el nivel sube a 2 y se spawnea exactamente un
      cuadrado del cielo.
- [x] 4.3 Añadir test: recolectar un cuadrado del cielo suma +1 moneda (y no suma vida).
- [x] 4.4 Añadir test: `Cloud.render` con `sprite` dibuja píxeles de nube distintos a la elipse
      (o que usa el sprite); sin sprite sigue dibujando la elipse.
- [x] 4.5 Añadir test: `_render_game` del variante Face pinta el fondo con `SKY_COLOR` (celeste).
- [x] 4.6 Ejecutar la suite completa: `python3 -m pytest tests/ -q` y confirmar que los tests de
      `test_game.py` y `test_mario_game.py` siguen verdes.

## 5. Verificación manual

- [ ] 5.1 `./run_mario_face.sh`: las nubes se ven como nubes (sprite), el cielo es celeste, la
      velocidad sube de 1.0x → 1.1x → 1.2x por nivel, cada 5 obstáculos aparece un bloque de
      interrogación que da +1 moneda, y el HUD acumula monedas de obstáculos + cuadrados.
