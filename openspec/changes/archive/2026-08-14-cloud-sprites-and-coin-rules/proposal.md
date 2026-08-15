## Why

En el Mario Face Jump las nubes se ven como óvalos blancos en lugar de nubes de
Mario: el `Cloud.render` dibuja una elipse simple. Además, las reglas de juego no
coinciden con lo pedido: la velocidad crece de forma multiplicativa (`×1.10^(nivel-1)`)
en vez de sumar `0.1` por nivel, y los bloques del cielo otorgan monedas en lugar de
vidas.

## What Changes

- El cielo durante el juego se renderiza de color **celeste** (azul claro).
- Las nubes del juego (capa en movimiento) se dibujan con un sprite de nube (recortado
  de `sprites/smb1_misc_sprites.gif`), no con una elipse simple. Las pantallas de MENÚ
  y GAME OVER conservan su fondo actual.
- La velocidad pasa a un multiplicador aditivo por nivel: `velocidad = base × (1 + 0.1 × (nivel-1))`.
  Ej: nivel 1 = `1.0x` (4.0), nivel 2 = `1.1x` (4.4), nivel 3 = `1.2x` (4.8), etc.
- Con el aumento de velocidad se mueve todo más rápido: obstáculos, nubes y cuadrados
  del cielo escalan con la velocidad actual del juego.
- Los cuadrados del cielo otorgan **+1 vida** (corazón) al recolectarlos, como en el
  Mario Bros base, hasta llegar al máximo de vidas.
  Aparece **1 cuadrado cada 5 obstáculos superados** (misma cadencia que el subir de nivel).
- Se introduce un contador de monedas acumulado: **1 moneda por obstáculo superado**.
  El HUD muestra el total acumulado.
- Cada 5 obstáculos superados se sube de nivel +1 (comportamiento ya existente, se mantiene).

## Capabilities

### New Capabilities

- `mario-face-jump-rules`: reglas de juego del variante Mario Face Jump — subir de nivel
  cada 5 obstáculos, acumulación de monedas (obstáculos superados), restauración de vida
  con los cuadrados del cielo, velocidad con multiplicador aditivo `+0.1` por nivel y
  avance de todos los elementos a la velocidad actual.

### Modified Capabilities

- `game-moving-clouds`: cambia el requisito de apariencia — durante el juego las nubes
  se renderizan con un sprite de nube (recortado del sprite sheet) en lugar de una elipse.
- `game-sky-blocks`: cambia el requisito de recolección — el cuadrado del cielo otorga
  **+1 vida** al recolectarlo (mantiene la restauración de vida del juego base) y su
  aparición se ata a la cadencia de **1 por cada 5 obstáculos superados**.

## Impact

- `src/game.py`: clase `Cloud.render` (o nueva variante sprite), clase `SkyBlock` (moneda
  en vez de vida, cadencia cada 5), constantes de cadencia y multiplicador de velocidad,
  color de cielo celeste.
- `src/mario_game.py`: constantes de velocidad (`SPEED_MULTIPLIER` → aditivo `0.1`),
  contador de monedas, spawn de cuadrados atado a los obstáculos superados, HUD.
- `src/mario_face_game.py`: herencia del engine base; sin cambios funcionales salvo que
  `_render_game` ya usa la capa de nubes en movimiento.
- `src/mario_face_main.py`: sin cambios.
- `sprites/`: se recorta/exporta un PNG de nube desde `smb1_misc_sprites.gif` (y opcionalmente
  un sprite de cuadrado tipo bloque de interrogación desde `SMW_v-ram-yane_QuestionMarkBlock.png`).
- Tests: `tests/test_mario_face_game.py`, `tests/test_game.py`, `tests/test_mario_game.py`.
