## 1. Add Minecraft rendering to SilhouetteDrawer

- [x] 1.1 Add Minecraft color constants (sky, grass, dirt, cloud, block border) to `src/silhouette.py`
- [x] 1.2 Add `_draw_oriented_rect()` helper to `SilhouetteDrawer` for thick oriented limb blocks
- [x] 1.3 Add `draw_minecraft_head()` method (square block: red cap top + peach face bottom + pixel eyes)
- [x] 1.4 Add `draw_minecraft_body()` method — 5 predefined solid rectangle segments (torso, 2 arms, 2 legs), NOT connection-based
- [x] 1.5 Wire `"minecraft_head"` and `"minecraft_body"` into `render_character()` dispatch
- [x] 1.6 Add tests in `tests/test_silhouette.py` for Minecraft head/body rendering
- [x] 1.7 Add fixed-scale cap (`MAX_SCALE`) to prevent character enlargement on partial pose; character remains still ("quieto") when detection lost
- [x] 1.8 Add shoulder-width range check (`MIN_SHOULDER_WIDTH`, `MAX_SHOULDER_WIDTH`) + `_scale_warning` flag for detection quality
- [x] 1.9 Add limb endpoint constraints (`_constrain_limbs`) — clamp wrists/heels to max extension from joints so character never deforms
- [x] 1.10 Add `_render_warning()` in game engine — "ACERQUE O ALEJE LA CAMARA" message at top when detection poor
- [x] 1.11 Gate jump detection on `!scale_warning` — jumps only fire when pose quality is good

## 2. Create Minecraft game engine module

- [x] 2.1 Create `src/minecraft_game.py` skeleton with imports and constants
- [x] 2.2 Implement `MinecraftMarioCharacter` with Minecraft rendering styles, fixed-size scale (MAX_SCALE cap), and "remain still" behavior when detection is poor
- [x] 2.3 Implement `MinecraftObstacle` with type field and voxel-style rendering (pipe, block, goomba)
- [x] 2.4 Implement `MinecraftObstacleManager` with level tracking, progressive gap tightening, type cycling
- [x] 2.5 Implement `MinecraftGameEngine` with _render_background (sky, pixel clouds, grass-block ground), level-up overlay, Minecraft HUD

## 3. Create entry point and launch script

- [x] 3.1 Create `src/minecraft_main.py` (mirrors mario_main.py pattern)
- [x] 3.2 Create `run_minecraft.sh` (mirrors run_mario.sh, forwards "$@")
- [x] 3.3 Make `run_minecraft.sh` executable

## 4. Tests

- [x] 4.1 Create `tests/test_minecraft_game.py` mirroring `test_mario_game.py` patterns
- [x] 4.2 Test `_draw_oriented_rect` helper: vertical, horizontal, diagonal vectors
- [x] 4.3 Test MinecraftMarioCharacter: jump physics, bbox, reset, apex, fixed-size scale, no-enlarge, remain-still, scale-warning (too close/far/clears), rendering styles
- [x] 4.4 Test MinecraftObstacle: movement, collision, render by type (voxel rectangles)
- [x] 4.5 Test MinecraftObstacleManager: level progression, gap tightening, type cycling, reset
- [x] 4.6 Test MinecraftGameEngine: states, jump detection, jump-gating on warning, collision, background color, level-up, HUD, warning message rendering

## 5. OpenSpec artifacts

- [x] 5.1 Create `openspec/changes/mario-minecraft-character/.openspec.yaml`
- [x] 5.2 Create `proposal.md`
- [x] 5.3 Create `design.md`
- [x] 5.4 Create `specs/mario-minecraft-character/spec.md`
- [x] 5.5 Create `tasks.md`

## 6. Documentation

- [x] 6.1 Update `README.md` with "## Minecraft Mario Game" section

## 7. Verification

- [x] 7.1 Run `pytest tests/test_minecraft_game.py -v` — 49 tests, all pass
- [x] 7.2 Run `pytest tests/test_silhouette.py -v` — 44 tests, all pass (no regressions)
- [x] 7.3 Run `pytest tests/ -v` — 251 tests, full suite passes, no regressions
- [x] 7.4 Run `openspec validate mario-minecraft-character` — validates