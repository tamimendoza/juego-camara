## Why

The existing pose jump game renders the webcam person as a grayscale stick figure
on a solid black background with obstacles spawning every 40–90 frames. This is
too difficult for new players — the character barely clears obstacles and the
gaps are tight. A Mario Bros-themed variant addresses this by:

1. Applying a familiar Mario Bros aesthetic (sky-blue background, clouds, bushes,
   brick ground, pipes, blocks, goombas) so the game is visually engaging.
2. Rendering the webcam-detected character with Mario's colour palette (red cap,
   peach face, red shirt, blue overalls) while still mirroring the person's
   actual pose and jump — preserving the de-identification stick-figure approach
   the project prefers.
3. Making obstacles more separated at the start (level 1: 150–250 frame gaps vs
   the existing 40–90) so players can advance through levels, with progressive
   tightening every 30 obstacles.

## What Changes

- **Add Mario rendering methods** to `SilhouetteDrawer` (`draw_mario_head`,
  `draw_mario_body`) with new style strings `"mario_head"` and `"mario_body"`
  dispatched in `render_character()`.
- **Create `src/mario_game.py`** — Mario game engine with:
  - `MarioCharacter`: miniatura character using Mario palette, reuses
    `JumpDetector` and pose-to-miniatura transformation from `game.py`.
  - `MarioObstacle`: obstacle with a `type` field ("pipe", "block", "goomba")
    and type-specific rendering.
  - `MarioObstacleManager`: spawns obstacles, tracks level, tightens spawn gaps
    every 30 obstacles passed.
  - `MarioGameEngine`: game state manager with sky-blue background, clouds,
    bushes, brick ground, level-up overlay, and Mario-themed HUD.
- **Create `src/mario_main.py`** — entry point mirroring `game_main.py`.
- **Create `run_mario.sh`** — launch script mirroring `run_game.sh`.
- **Add tests** in `tests/test_mario_game.py` and `tests/test_silhouette.py`.
- **Update `README.md`** with a Mario Bros Game section.

## Capabilities

### New Capabilities

- `mario-bros-variant`: A Mario Bros-themed pose jump game variant with
  Mario-coloured stick-figure character, themed background, type-varied
  obstacles, and level-based progressive difficulty.

### Modified Capabilities

- `pose-jump-game` rendering: `SilhouetteDrawer` gains `draw_mario_head()` and
  `draw_mario_body()` methods and new style strings (`mario_head`, `mario_body`)
  in `render_character()`. No existing rendering behaviour is changed.

## Impact

- **Modified**: `src/silhouette.py` — adds Mario colour constants, two new
  drawing methods, and two new style strings in the dispatch.
- **New**: `src/mario_game.py`, `src/mario_main.py`, `run_mario.sh` — Mario game
  variant.
- **New**: `tests/test_mario_game.py` — 52 unit tests for Mario game components.
- **Modified**: `tests/test_silhouette.py` — adds Mario head/body rendering tests.
- **Modified**: `README.md` — documents the new Mario game mode.
- **New**: `openspec/changes/mario-bros-variant/` — OpenSpec change artifacts.
