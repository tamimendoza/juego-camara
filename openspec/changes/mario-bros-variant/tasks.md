## 1. Add Mario rendering to SilhouetteDrawer

- [x] 1.1 Add Mario colour constants (face, hat, hair, shirt, overall) to `src/silhouette.py`
- [x] 1.2 Add `draw_mario_head()` method (peach face + red cap + brown hair arc)
- [x] 1.3 Add `draw_mario_body()` method (red shirt lines for arms/torus, blue overall lines for legs)
- [x] 1.4 Wire `"mario_head"` and `"mario_body"` into `render_character()` dispatch
- [x] 1.5 Add tests in `tests/test_silhouette.py` for Mario head/body rendering

## 2. Create Mario game engine module

- [x] 2.1 Create `src/mario_game.py` skeleton with imports and constants
- [x] 2.2 Implement `MarioCharacter` (reuses PlayerCharacter physics, Mario rendering styles)
- [x] 2.3 Implement `MarioObstacle` with type field and type-specific rendering (pipe, block, goomba)
- [x] 2.4 Implement `MarioObstacleManager` with level tracking, progressive gap tightening, type cycling
- [x] 2.5 Implement `MarioGameEngine` with _render_background (sky, clouds, bushes, bricks), level-up overlay, Mario HUD

## 3. Create entry point and launch script

- [x] 3.1 Create `src/mario_main.py` (mirrors game_main.py pattern)
- [x] 3.2 Create `run_mario.sh` (mirrors run_game.sh, forwards "$@")
- [x] 3.3 Make `run_mario.sh` executable

## 4. Tests

- [x] 4.1 Create `tests/test_mario_game.py` mirroring `test_game.py` patterns
- [x] 4.2 Test MarioCharacter: jump physics, bbox, reset, apex, rendering
- [x] 4.3 Test MarioObstacle: movement, collision, render by type
- [x] 4.4 Test MarioObstacleManager: level progression, gap tightening, type cycling, reset
- [x] 4.5 Test MarioGameEngine: states, jump detection, collision, background color, level-up, HUD

## 5. OpenSpec artifacts

- [x] 5.1 Create `openspec/changes/mario-bros-variant/.openspec.yaml`
- [x] 5.2 Create `proposal.md`
- [x] 5.3 Create `design.md`
- [x] 5.4 Create `tasks.md`
- [x] 5.5 Create `specs/mario-bros-variant/spec.md`

## 6. Documentation

- [x] 6.1 Update `README.md` with "## Mario Bros Game" section

## 7. Verification

- [x] 7.1 Run `pytest tests/test_mario_game.py -v` — all pass
- [x] 7.2 Run `pytest tests/test_silhouette.py -v` — all pass
- [x] 7.3 Run `pytest tests/ -v` — full suite passes, no regressions
