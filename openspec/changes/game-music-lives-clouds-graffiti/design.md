## Context

See proposal.md — Why.

The codebase has three game variants sharing a common pose-detection pipeline:

- `src/game.py` — Base pose jump game. Solid black background, no clouds, no ground
  rendering. `LEVEL_INTERVAL = 10` (recently changed from 30 in the
  `level-up-every-10-blocks` change).
- `src/mario_game.py` — Mario Bros variant. Sky background, static clouds, bushes,
  brick-patterned ground. `LEVEL_INTERVAL = 10`.
- `src/minecraft_game.py` — Minecraft voxel variant. Sky background, pixel clouds,
  grass/dirt ground. `LEVEL_INTERVAL = 10`.

All three engines compute speed via `SPEED_MULTIPLIER^(level - 1)`. The
`SoundManager` (`src/sound_manager.py`) currently only plays coin and game-over
sounds via `pygame.mixer.Sound`. The `sounds/` directory contains
`GroundTheme.mp3` and `InvincibilityTheme.mp3` (Mario-themed background music).

## Goals / Non-Goals

**Goals:**
- Play `GroundTheme.mp3` as continuous background music during gameplay, with
  volume mixing that keeps music below SFX levels.
- Play `InvincibilityTheme.mp3` when score >= 5 coins, layered on top of
  background music.
- Change `LEVEL_INTERVAL` from 10 to 5 across all three game variants.
- Add a 3-life system with visible hearts; collision costs a life; game over at
  0 lives.
- Add sky blocks that grant lives (max 3) when touched by the jumping character.
- Animate clouds to drift leftward (parallax, slower than obstacles).
- Render brick-colored ground with graffiti text "Familia Mendoza Silva".
- Pause the game with "Acerquese o alejese de la camara" warning when pose
  detection degrades (too few landmarks or out-of-range shoulder width).
- Ensure passed obstacles do not trigger collision detection.
- Enable mid-air jump (double jump) when the character is airborne and the user
  jumps again, capped at 2 total jumps per airtime.

**Non-Goals:**
- No changes to the pose detection pipeline (`pose_detector.py`, `camera.py`).
- No new CLI arguments or camera handling changes.
- No changes to the Minecraft variant's voxel rendering style — only the
  shared game mechanics (lives, music, level interval, clouds, ground, graffiti)
  are added.
- No changes to the `JumpDetector` detection logic — double jump remains as-is.

## Decisions

### Decision 1: Background music via pygame.mixer.music

**Choice:** Use `pygame.mixer.music` for background music (streaming) and
`pygame.mixer.Sound` for sound effects (short clips). Set music volume to 0.3
and SFX volume to 0.7 so music never overpowers effects.

**Rationale:** `pygame.mixer.music` is designed for continuous playback and
supports volume control independently from `Sound` objects. This satisfies the
requirement that background music not be louder than sound effects.

**Alternative considered:** Use `pygame.mixer.Sound` for everything. Rejected —
`Sound` objects load the entire file into memory, which is wasteful for
multi-minute background tracks.

### Decision 2: Level interval change from 10 to 5

**Choice:** Change `LEVEL_INTERVAL` from 10 to 5 in all three game variants
(`game.py`, `mario_game.py`, `minecraft_game.py`). The speed formula
`SPEED_MULTIPLIER^(level - 1)` already ties speed to level, so no formula change
is needed — only the interval constant.

**Rationale:** The user explicitly requests "cada 5 monedas debe subir el nivel."
The existing speed formula already works with any `LEVEL_INTERVAL` value.

### Decision 3: Lives system as hearts in HUD

**Choice:** Add a `lives` field to each game engine (starting at 3). Render 3
hearts in the top-left HUD area. On collision, decrement `lives` by 1 and remove
one heart. When `lives` reaches 0, transition to GAME_OVER. On restart, reset to 3.

**Rationale:** Simple, visible, and matches the user's request for "3 corazones"
that "van desapareciendo."

**Alternative considered:** End the game immediately on collision (current
behavior). Rejected — the user explicitly wants a lives system with hearts.

### Decision 4: Sky blocks as collectible life items

**Choice:** Add a `SkyBlock` class (similar to `Obstacle`) that spawns at random
x positions in the upper sky region (y < ground_y). Each block has a bounding box.
When the character's bounding box overlaps a block during a jump, increment lives
(capped at 3), play coin sound, and remove the block.

**Rationale:** Reuses the existing collision detection pattern from `Obstacle`.
The character is at the bottom of the screen, so touching a sky block requires
a successful jump — rewarding skill.

### Decision 5: Moving clouds via horizontal offset

**Choice:** Add a `_cloud_offset` field to each engine that increments each frame
and wraps around. Cloud x positions are offset by `_cloud_offset` at render time.
Drift speed is set to ~50% of the base obstacle speed for parallax depth.

**Rationale:** Simple horizontal scroll creates the illusion of forward motion
without complex animation logic.

### Decision 6: Brick ground rendering

**Choice:** For the base game (`game.py`), add brick ground rendering similar to
the Mario variant. For the Mario variant, the ground already has a brick pattern —
ensure it uses the brick color. For the Minecraft variant, add brick ground
rendering. Draw graffiti text "Familia Mendoza Silva" on the ground using
`cv2.putText`.

**Rationale:** The user wants "color de ladrillos" on the ground. The Mario
variant already has this; the base and Minecraft variants need it added.

### Decision 7: Pose stability pause

**Choice:** Reuse the Minecraft variant's `scale_warning` pattern (shoulder width
range check) across all three variants. When detection quality is poor, pause
obstacle spawning and character pose updates, but keep rendering the frozen
frame with the warning text. The character retains its last known pose.

**Rationale:** The Minecraft variant already implements this pattern
(`MIN_SHOULDER_WIDTH`, `MAX_SHOULDER_WIDTH`, `scale_warning`). Extending it to
all variants ensures consistency.

### Decision 8: Passed obstacle collision safety

**Choice:** The existing `Obstacle.mark_passed()` and `Obstacle.passed` flag
already prevent re-counting. The `check_collision()` method should also skip
obstacles that are already marked as `passed`, ensuring no collision is detected
for obstacles that have already been cleared.

**Rationale:** The user explicitly requests "cuida que cuando pasamos un obstaculo
no se cruce con la persona porque ya sono el punto ganado" — after an obstacle is
passed, it should not collide with the character.

## Risks / Trade-offs

- **[Risk] Level interval change (10 → 5) makes the game harder faster.**
  → Mitigation: Speed increases compound, but the user explicitly requested
  5-coin intervals. The spawn gap ranges in Mario/Minecraft variants can be
  adjusted if needed.

- **[Risk] Sky blocks may be too easy to collect (character could touch them
  while on the ground).**
  → Mitigation: Sky blocks are placed in the upper sky region (y < ground_y).
  The character is at the bottom of the screen. Only a jump can reach them.

- **[Risk] Background music may not work in headless/CI environments.**
  → Mitigation: `pygame.mixer.music` degrades gracefully; if initialization
  fails, music simply doesn't play. The game runs without music.

- **[Risk] Moving clouds may impact performance on low-end hardware.**
  → Mitigation: Cloud rendering is simple offset arithmetic — negligible cost.

- **[Risk] Mid-air jump may make the game too easy.**
  → Mitigation: `MAX_JUMPS = 2` cap and existing `JUMP_COOLDOWN` on the
  `JumpDetector` prevent spamming. The double jump is most effective when used
  near the apex of the first jump.

## Migration Plan

1. Extend `SoundManager` to support background music via `pygame.mixer.music`.
2. Change `LEVEL_INTERVAL` from 10 to 5 in all three game variants.
3. Add lives system (hearts) to all three game engines.
4. Add sky blocks to all three game engines.
5. Add moving clouds to Mario and Minecraft variants (base game gets clouds too).
6. Add brick ground rendering to base and Minecraft variants.
7. Add graffiti text to all three variants.
8. Add pose stability pause to base and Mario variants (Minecraft already has it).
9. Fix passed-obstacle collision safety in `Obstacle.check_collision()`.
10. Ensure mid-air jump (double jump) is enabled in all three variants.
11. Update tests for all changes.
12. Update README.md.

Rollback: Revert `LEVEL_INTERVAL` to 10, remove lives/sky blocks/clouds/ground/
graffiti/music additions, restore original collision behavior, disable mid-air
jump.

## Open Questions

- Whether the base game (`game.py`) should get a sky background with clouds, or
  remain solid black with brick ground. → Assumption: Add a simple sky background
  with clouds and brick ground to the base game for consistency.
