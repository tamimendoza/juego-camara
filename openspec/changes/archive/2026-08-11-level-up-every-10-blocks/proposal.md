## Why

The current level and speed progression system is inconsistent across the three
game variants. The base pose jump game (`game.py`) has no level system at all —
it only increases speed every 10 obstacles. The Mario and Minecraft variants
(`mario_game.py`, `minecraft_game.py`) increment levels every 30 obstacles with
speed increasing separately every 10 obstacles. The user wants a unified
progression model: every 10 obstacles cleared should trigger a level-up, and
speed should begin increasing from level 2 onward, ramping gradually.

## What Changes

- **Add level system to the base game** (`src/game.py`): `GameEngine` and
  `ObstacleManager` gain a `level` property that increments every 10 obstacles
  passed. Level 1 = 0–9 obstacles, level 2 = 10–19, etc. The existing speed
  formula (`BASE_SPEED * SPEED_MULTIPLIER^(passed_count // 10)`) already aligns
  with this — speed stays at base during level 1 and begins multiplying from
  level 2. Level is displayed in the HUD and game-over screen.

- **Unify level interval to 10 blocks in Mario/Minecraft variants**: Change
  `LEVEL_INTERVAL` from 30 to 10 in both `mario_game.py` and
  `minecraft_game.py`. Expand `LEVEL_SPAWN_GAP_RANGES` to 6 levels (instead of
  5) with finer-grained tightening steps so the difficulty curve remains
  balanced at the faster 10-block cadence.

- **Make speed explicitly level-driven**: Refactor the speed formula in all
  three engines to use `SPEED_MULTIPLIER^(level - 1)` (or equivalently
  `(passed_count // 10)`), so speed is unambiguously tied to the level. Level 1
  → no speed increase; level 2 → first multiplier; level N → multiplier^N.

- **Update HUD rendering** in all three engines to display the current Level
  alongside score and speed.

- **Update tests** in `tests/test_game.py`, `tests/test_mario_game.py`,
  `tests/test_minecraft_game.py` to validate 10-block level intervals, level-
  based speed, and level display in the HUD.

- **Update README.md** docstrings and speed/level progression documentation.

### Modified Capabilities

- `pose-jump-game`: Level-up interval changes from no-levels (base game) /
  30-block (Mario/Minecraft) to 10-block uniform across all variants. Speed now
  explicitly tied to level (starts increasing at level 2). Level displayed in
  HUD.

## Capabilities

### New Capabilities

(none — all changes modify existing capabilities)

### Modified Capabilities

- `pose-jump-game`: Level progression interval unified to 10 obstacles; speed
  progression tied to level (increases from level 2); level displayed in HUD.

## Impact

- **Modified**: `src/game.py` — `ObstacleManager` gains `level` property and
  `LEVEL_INTERVAL`; `GameEngine` gains `level` property and displays level in
  HUD and game-over screen.
- **Modified**: `src/mario_game.py` — `LEVEL_INTERVAL` changed from 30 to 10;
  `LEVEL_SPAWN_GAP_RANGES` expanded from 5 to 6 levels; speed formula tied to
  level.
- **Modified**: `src/minecraft_game.py` — same changes as `mario_game.py`.
- **Modified**: `tests/test_game.py`, `tests/test_mario_game.py`,
  `tests/test_minecraft_game.py` — updated level/speed progression tests.
- **Modified**: `README.md` — updated documentation.
- **No breaking changes** to APIs or CLI. All changes are internal game
  constants and properties.