## Context

The codebase has three game variants sharing a common pose-detection pipeline:

- `src/game.py` — Base pose jump game. Has speed progression every 10 obstacles
  (`BASE_SPEED * SPEED_MULTIPLIER^(passed_count // 10)`) but no level system.
- `src/mario_game.py` — Mario Bros variant. Has level progression every 30
  obstacles (`LEVEL_INTERVAL = 30`) controlling spawn-gap tightening, plus
  independent speed progression every 10 obstacles.
- `src/minecraft_game.py` — Minecraft voxel variant. Mirrors the Mario game
  structure with the same 30-block level interval.

All three engines compute speed via the same formula on `GameEngine.speed` /
`MarioGameEngine.speed` / `MinecraftGameEngine.speed`. The `ObstacleManager`
(or `MarioObstacleManager` / `MinecraftObstacleManager`) tracks
`_passed_count` and, in the Mario/Minecraft variants, `_level`.

## Goals / Non-Goals

**Goals:**
- Unify level increment to every 10 obstacles across all three game variants.
- Add level display to the base game's HUD and game-over screen.
- Tie speed progression explicitly to `level - 1` so level 1 = base speed and
  level 2 = first speed increase.
- Expand Mario/Minecraft spawn gap ranges for the faster 10-block cadence.

**Non-Goals:**
- No restructuring of the pose detection, character rendering, or obstacle
  classes beyond the level/speed constants and properties.
- No new game variants or visual themes.
- No changes to CLI arguments, camera handling, or the main silhouette app.

## Decisions

### Decision 1: Level = passed_count // 10 + 1 (uniform across all games)

All three games use `LEVEL_INTERVAL = 10` (= `SPEED_INTERVAL`). Level is computed
as `(passed_count // LEVEL_INTERVAL) + 1`, giving level 1 at 0–9 obstacles,
level 2 at 10–19, etc.

**Rationale:** This directly satisfies the user's requirement "cada 10 bloques
debe subir de nivel." The value 10 already exists as `SPEED_INTERVAL`, so we
introduce `LEVEL_INTERVAL` referencing the same value for semantic clarity.

**Alternative considered:** Keep separate constants. Rejected — both intervals
are always 10, and coupling them prevents future drift.

### Decision 2: Speed multiplier = SPEED_MULTIPLIER^(level - 1)

The speed formula changes from `SPEED_MULTIPLIER^(passed_count // 10)` to
`SPEED_MULTIPLIER^(level - 1)`. Since `level - 1 == passed_count // 10`, the
numerical result is identical — but the code now explicitly documents that
speed increases from level 2 onward.

**Rationale:** Makes the "from level 2, speed increases" requirement
self-documenting in the code. Level 1 → multiplier^0 = 1.0 (base speed). Level 2
→ multiplier^1 (first increase).

### Decision 3: Expand spawn gap ranges for 10-block cadence in Mario/Minecraft

The existing 5-level gap table was designed for 30-block intervals (reaching max
at 120 obstacles). With 10-block intervals, that same table would cap at 40
obstacles — too fast. We expand to 6 levels:

| Level | Range (frames) | Reached at |
|-------|----------------|------------|
| 1     | 180–280        | 0 obs      |
| 2     | 150–250        | 10         |
| 3     | 130–230        | 20         |
| 4     | 110–200        | 30         |
| 5     | 90–170         | 40         |
| 6+    | 70–130         | 50+ (cap)  |

**Rationale:** Finer granularity matches the faster level-up cadence. Speed
multipliers compound with tighter gaps for a smooth difficulty curve.

### Decision 4: Add level to base game (game.py)

The base game currently has no level concept. We add:
- `LEVEL_INTERVAL = 10` constant
- `ObstacleManager.level` property (`passed_count // LEVEL_INTERVAL + 1`)
- `GameEngine.level` property (delegates to `ObstacleManager`)
- Level displayed in `_draw_hud` and `_render_game_over`

**Rationale:** The base game should match the Mario/Minecraft progression model
for consistency.

## Risks / Trade-offs

- **[Risk] Mario/Minecraft difficulty ramps faster.** With 10-block (vs 30-block)
  levels, players hit max difficulty sooner.
  → Mitigation: Expanded spawn gap ranges (6 levels) provide a smoother curve;
  combined with gradual speed increases this balances the faster level cadence.

- **[Risk] Tests referencing LEVEL_INTERVAL=30 and 5-level tables will break.**
  → Mitigation: All affected tests updated to reflect 10-block intervals and new
  gap ranges.

## Migration Plan

This is a behavior change to existing games, not a data migration:

1. Modify `src/game.py` — add `LEVEL_INTERVAL`, `level` property, HUD display.
2. Modify `src/mario_game.py` — change `LEVEL_INTERVAL` to 10, expand gap ranges.
3. Modify `src/minecraft_game.py` — same as mario_game.py.
4. Update `tests/test_game.py`, `tests/test_mario_game.py`,
   `tests/test_minecraft_game.py`.
5. Update docstrings and README.

Rollback: revert the constant changes and level properties; gap ranges revert to
original 5-level table.

## Open Questions

(none)