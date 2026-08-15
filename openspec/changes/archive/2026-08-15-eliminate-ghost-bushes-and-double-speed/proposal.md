## Why

El Mario Face Jump renderiza los arbustos estáticos a posiciones fijas pensadas para
640×480 (y≈400), pero el variante corre a 1280×720 donde la línea de tierra está en
y=612 — por eso quedan arbustos "fantasma" flotando en el aire. Además, el variante
Face sobrescribe la velocidad con una fórmula aditiva lenta (`+0.1` por nivel), lo
que hace que cada nivel se sienta muy lento comparado con el juego base, que ya
duplica la velocidad por nivel (`SPEED_MULTIPLIER = 2.0`).

## What Changes

- Las posiciones de los elementos estáticos del entorno (arbustos y nubes estáticas)
  pasan a calcularse de forma **relativa a la resolución** (altura de la línea de
  tierra), de modo que los arbustos descansen sobre el suelo y las nubes queden en el
  cielo sin importar la resolución (640×480 y 1280×720).
- La velocidad del **Mario Face Jump** deja de usar el multiplicador aditivo
  `1 + 0.1 × (nivel − 1)` y pasa al multiplicador multiplicativo
  `SPEED_MULTIPLIER = 2.0` (el mismo del juego base): el doble de rápido por cada
  nivel superado.
- El HUD y la pantalla de GAME OVER del variante Face muestran el multiplicador
  multiplicativo `2.0^(nivel − 1)` en lugar del aditivo.

## Capabilities

### New Capabilities

(Empty – no new capabilities.)

### Modified Capabilities

- **mario-face-jump-rules** – Cambia el requisito *Additive speed multiplier* por
  uno *multiplicativo*: la velocidad se duplica por nivel (factor `2.0`), igual que
  el juego base.
- **mario-bros-variant** – Actualiza la escena de velocidad: el multiplicador por
  nivel pasa de `1.10` a `2.0` (doble por nivel).
- **mario-face-capture** – Actualiza el requisito *Speed progression* (heredado del
  variante Mario): el multiplicador pasa de `1.10` a `2.0`.
- **mario-minecraft-character** – Actualiza el requisito *Speed progression*
  (heredado del variante Mario): el multiplicador pasa de `1.10` a `2.0`.

## Impact

- `src/games/mario/mario_game.py`: `_BUSH_OFFSETS`/`_CLOUD_OFFSETS` se derivan de
  la resolución (`_ground_y`) en `_render_static_environment`.
- `src/games/mario/mario_face_game.py`: `SPEED_INCREMENT` se reemplaza por
  `SPEED_MULTIPLIER = 2.0`; la property `speed`, `_draw_hud` y `_render_game_over`
  usan la fórmula multiplicativa.
- Tests: `tests/games/test_mario_face_game.py` (velocidad multiplicativa, arbustos
  sobre el suelo a 720p), `tests/games/test_mario_game.py` y
  `tests/framework/test_jump_game.py` (sin cambios, ya esperan 2.0).
