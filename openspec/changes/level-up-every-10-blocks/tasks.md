## 1. Base game (game.py) — add level system

- [x] 1.1 Add `LEVEL_INTERVAL = 10` constant alongside `SPEED_INTERVAL`
- [x] 1.2 Add `level` property to `ObstacleManager` (`passed_count // LEVEL_INTERVAL + 1`)
- [x] 1.3 Refactor `GameEngine.speed` to use `SPEED_MULTIPLIER ** (level - 1)` for semantic clarity
- [x] 1.4 Add `level` property to `GameEngine` (delegate to `ObstacleManager`)
- [x] 1.5 Display level in `_draw_hud` (top-left HUD)
- [x] 1.6 Display level in `_render_game_over` screen
- [x] 1.7 Update docstring and module comments

## 2. Mario Bros variant (mario_game.py) — unify level interval

- [x] 2.1 Change `LEVEL_INTERVAL` from 30 to 10
- [x] 2.2 Expand `LEVEL_SPAWN_GAP_RANGES` from 5 to 6 levels (finer granularity for 10-block cadence)
- [x] 2.3 Refactor `MarioGameEngine.speed` to use `SPEED_MULTIPLIER ** (level - 1)`
- [x] 2.4 Update docstring and comments referencing 30-block intervals
- [x] 2.5 Verify `_check_level_up` uses updated `LEVEL_INTERVAL` (no code change needed, just verification)

## 3. Minecraft variant (minecraft_game.py) — unify level interval

- [x] 3.1 Change `LEVEL_INTERVAL` from 30 to 10
- [x] 3.2 Expand `LEVEL_SPAWN_GAP_RANGES` from 5 to 6 levels
- [x] 3.3 Refactor `MinecraftGameEngine.speed` to use `SPEED_MULTIPLIER ** (level - 1)`
- [x] 3.4 Update docstring and comments referencing 30-block intervals
- [x] 3.5 Verify `_check_level_up` uses updated `LEVEL_INTERVAL`

## 4. Update tests

- [x] 4.1 Update `tests/test_game.py`: add level progression tests, update speed tests, add level HUD checks
- [x] 4.2 Update `tests/test_mario_game.py`: update level progression interval from 30 to 10, update gap range assertions, update speed tests
- [x] 4.3 Update `tests/test_minecraft_game.py`: same updates as mario tests

## 5. Documentation

- [x] 5.1 Update README.md speed/level progression sections for all three games
- [x] 5.2 Update module docstrings in `src/mario_main.py` and `src/minecraft_main.py`

## 6. Verification

- [x] 6.1 Run `pytest tests/test_game.py -v` — all pass
- [x] 6.2 Run `pytest tests/test_mario_game.py -v` — all pass
- [x] 6.3 Run `pytest tests/test_minecraft_game.py -v` — all pass
- [x] 6.4 Run `pytest tests/ -v` — full suite passes, no regressions
- [x] 6.5 Run `openspec validate --change level-up-every-10-blocks`