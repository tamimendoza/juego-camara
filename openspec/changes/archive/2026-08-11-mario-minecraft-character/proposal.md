## Why

The existing `mario-bros-variant` renders the pose-driven character with smooth
cv2 primitives: a filled circle for the face, an ellipse for the cap, and
single-pixel-width lines for the body. While this conveys Mario's colors
(red cap, peach face, red shirt, blue overalls), it does not capture the
**blocky, voxel-based aesthetic** of Minecraft — where every body part is a
rectangular cube and the world is built from stacked blocks.

A Mario character designed in the Minecraft style bridges both franchises:
Mario's iconic color palette and silhouette, but rendered as the rectangular
"blocks" that define Minecraft's Steve/Alex player model. Retrieved reference
data from the official Minecraft Wiki describes Steve as having **wide arms,
dark brown hair, a cyan shirt, dark blue pants, and visible nose/eyes** — all
rendered as pixelated rectangular boxes (8×8 head, 4×12 limbs in the 16×16
skin grid).

The goal is a new game variant where:

1. The webcam-detected pose is rendered as a **blocky Mario miniatura** — each
   body part is a filled rectangle (voxel) rather than a line or circle, with
   Mario's red cap/face/shirt and blue overalls.
2. The background is a **Minecraft-style terrain**: sky-blue fill, pixelated
   clouds, a grass-block ground band (green top + brown dirt sides).
3. Obstacles reuse the existing Mario obstacle types (pipes, blocks, goombas)
   but could optionally include Minecraft-style mobs (e.g., Creeper green).

## What Changes

- **Add Minecraft rendering methods** to `SilhouetteDrawer`
  (`draw_minecraft_head`, `draw_minecraft_body`) with new style strings
  `"minecraft_head"` and `"minecraft_body"` dispatched in `render_character()`.
- **Create `src/minecraft_game.py`** — Minecraft-themed game engine with:
  - `MinecraftMarioCharacter`: blocky Mario miniatura using rectangular-voxel
    rendering, reuses `JumpDetector` and pose-to-miniatura transformation
    from `mario_game.py`.
  - `MinecraftObstacle`: obstacle with type-specific block rendering (pipe,
    block, goomba — same types, voxel-style rectangles).
  - `MinecraftObstacleManager`: spawns obstacles, level-based progressive
    tightening, type cycling (same progression as Mario variant).
  - `MinecraftGameEngine`: game state manager with sky-blue background,
    pixel clouds, grass-block ground, block HUD.
- **Create `src/minecraft_main.py`** — entry point mirroring `mario_main.py`.
- **Create `run_minecraft.sh`** — launch script mirroring `run_mario.sh`.
- **Add tests** in `tests/test_minecraft_game.py` and
  `tests/test_silhouette.py`.
- **Update `README.md`** with a "Minecraft Mario Game" section.

## Capabilities

### New Capabilities

- `minecraft-mario-character`: A Minecraft/voxel-style Mario Bros game variant
  with blocky rectangular-character rendering, Minecraft terrain background,
  and pose-driven jump mechanics.

### Modified Capabilities

- `SilhouetteDrawer` rendering: gains `draw_minecraft_head()` and
  `draw_minecraft_body()` methods and new style strings (`minecraft_head`,
  `minecraft_body`) in `render_character()`. No existing rendering behaviour is
  changed — these are opt-in style strings only.

## Impact

- **Modified**: `src/silhouette.py` — adds Minecraft color constants, two new
  drawing methods, and two new style strings in the dispatch.
- **New**: `src/minecraft_game.py`, `src/minecraft_main.py`, `run_minecraft.sh`
  — Minecraft Mario game variant.
- **New**: `tests/test_minecraft_game.py` — unit tests for Minecraft game
  components.
- **Modified**: `tests/test_silhouette.py` — adds Minecraft head/body rendering
  tests.
- **Modified**: `README.md` — documents the new Minecraft Mario game mode.
- **New**: `openspec/changes/mario-minecraft-character/` — OpenSpec change
  artifacts.
