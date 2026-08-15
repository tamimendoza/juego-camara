## Context

Ver propuesta (`proposal.md` – Why). Estado actual relevante:

- `src/games/mario/mario_game.py` define `_BUSH_OFFSETS` y `_CLOUD_OFFSETS` como
  listas de posiciones **absolutas** pensadas para 640×480 (`GROUND_Y_RATIO = 0.85`
  → `ground_y = 408`; arbustos en y≈395–410, nubes estáticas en y≈60–90).
- El variante Face (`mario_face_game.py`) hereda `_render_static_environment` de
  `MarioGameEngine` pero corre a `FACE_RESOLUTION = (1280, 720)` → `ground_y = 612`.
  Los arbustos estáticos (y≈395–410) quedan flotando en el aire.
- `MarioFaceGameEngine` sobrescribe `speed` con la fórmula aditiva
  `BASE_SPEED * (1 + SPEED_INCREMENT * (level - 1))` con `SPEED_INCREMENT = 0.1`
  (muy lenta), y `_draw_hud` / `_render_game_over` muestran ese multiplicador aditivo.
- El juego base (`src/framework/jump_game.py`) ya usa `SPEED_MULTIPLIER = 2.0`
  (multiplicativo) y `MarioGameEngine.speed` lo hereda.

## Goals / Non-Goals

**Goals:**
- Arbustos y nubes estáticas anclados a la resolución: los arbustos descansan sobre
  la línea de tierra y las nubes quedan en el cielo, tanto a 640×480 como a 1280×720.
- Mario Face Jump duplica su velocidad por nivel (`SPEED_MULTIPLIER = 2.0`), con el
  HUD y GAME OVER mostrando el multiplicador multiplicativo.

**Non-Goals:**
- No cambiar el comportamiento de nubes móviles, obstáculos, vidas, monedas, ni la
  detección de rostro/salto.
- No cambiar la dificultad de spawn (gaps por nivel) ni el `LEVEL_INTERVAL = 5`.
- No alterar el Minecraft (no tiene arbustos estáticos; solo hereda la velocidad).

## Decisions

### 1. Posiciones estáticas derivadas de `_ground_y`

**Decisión:** En `mario_game.py`, reemplazar las constantes `_BUSH_OFFSETS` /
`_CLOUD_OFFSETS` por funciones que generan posiciones relativas a la resolución:

- Arbustos: `y = ground_y - 8` (descansan justo sobre el suelo; la elipse de
  `_render_static_environment` tiene radio vertical ~12, así que su parte inferior
  queda a `ground_y + 4`, asentada en el suelo). `x` se reparte en el ancho con la
  misma distribución que hoy (proporcional a `width`).
- Nubes estáticas: `y ≈ ground_y * 0.18` (en el cielo, proporcional a la altura).

Se implementa como función `_bush_positions(width, ground_y)` /
`_cloud_positions(width, ground_y)` para que cualquier variante (base, Face) las
calcule según su resolución, sin duplicar lógica.

**Alternativas:** pasar `ground_y` como argumento a `_render_static_environment`
y escalar las listas fijas por un factor `height/480` → descartado porque introduce
un factor mágico y desalinea la distribución horizontal. Subclase en el Face con
offsets propios → descartado porque duplica la lógica de dibujo.

### 2. Velocidad multiplicativa en Mario Face Jump

**Decisión:** Reemplazar `SPEED_INCREMENT = 0.1` por `SPEED_MULTIPLIER = 2.0`
(importado/definido en `mario_face_game.py`) y cambiar la property `speed` a la
fórmula multiplicativa `BASE_SPEED * SPEED_MULTIPLIER ** (level - 1)`. Se actualizan
`_draw_hud` y `_render_game_over` para mostrar `2.0^(nivel−1)`.

**Alternativas:** eliminar el override y heredar `MarioGameEngine.speed` → descartado
por decisión del usuario ("Override with 2.0 multiplier"), mantiene el variante
autocontenido y sus tests explícitos.

## Risks / Trade-offs

- [Cambiar posiciones estáticas afecta a los tests de `test_mario_game.py`
  (`test_static_clouds_skipped_when_draw_clouds_false`, `test_graffiti_text_rendered`)] →
  los tests verifican regiones, no coordenadas exactas; se revisan y ajustan solo si
  fallan.
- [Velocidad 2.0 por nivel en el variante Face puede sentirse brusca] → es lo pedido
  ("doble de rápido por nivel") y consistente con el juego base; los gaps por nivel
  siguen siendo amplios en niveles bajos.
- [El variante Minecraft hereda `SPEED_MULTIPLIER` de `jump_game.py` (ya 2.0)] → sin
  cambios de código; solo se actualiza su spec para reflejar el valor real.

## Migration Plan

1. Refactor de posiciones estáticas en `mario_game.py` (funciones relativas).
2. Cambio de velocidad en `mario_face_game.py` (constante, `speed`, HUD, GAME OVER).
3. Actualizar tests (`test_mario_face_game.py`): velocidad multiplicativa y arbustos
   anclados al suelo a 720p.
4. Ejecutar `pytest -q` completo.
5. Rollback: revertir los dos archivos; los cambios son aislados y no rompen otros
   variantes (el base ya usaba 2.0; los arbustos vuelven a posiciones fijas).

## Open Questions

(ninguna)
