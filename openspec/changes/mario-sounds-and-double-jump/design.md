## Context

The Mario Bros variant (`src/mario_game.py`) reuses `JumpDetector` and physics
constants from the base game (`src/game.py`). The `MarioCharacter` class mirrors
`PlayerCharacter` but renders with Mario colours. Currently:

- `MarioCharacter.jump()` returns `False` if already airborne — no double jump.
- `MarioGameEngine._update_playing()` calls `self._player.jump()` when the
  `JumpDetector` fires, but has no audio component.
- `pygame` is already a project dependency (in `requirements.txt`) but is not
  used for audio anywhere in the codebase.
- The `sounds/` directory contains `mario-moneda.mp3` (coin sound) and
  `mario-bros-game-over-1.mp3` (game-over sound).

## Goals / Non-Goals

**Goals:**
- Play a coin sound when an obstacle is cleared (passed) during gameplay.
- Play a game-over sound when the character collides with an obstacle.
- Allow the Mario character to double-jump (second jump while airborne) for
  extra height, capped at 2 jumps so the character stays on screen.
- Degrade gracefully when audio is unavailable (no crash in headless/CI).
- All new code covered by unit tests; no regressions in existing suite.

**Non-Goals:**
- No background music or continuous soundtrack.
- No sound effects in the base game (`game.py`) or Minecraft variant
  (`minecraft_game.py`) — only the Mario Bros game.
- No changes to the `JumpDetector` detection logic — double jump is triggered
  by the same physical jump gesture detected a second time while airborne.
- No new dependencies — `pygame` is already installed.

## Decisions

### Decision 1: SoundManager as a separate module

**Choice:** Create `src/sound_manager.py` with a `SoundManager` class rather
than inlining `pygame.mixer` calls in `mario_game.py`.

**Rationale:** Separates audio concerns from game logic, makes the class
reusable for future game variants, and allows easy mocking in tests.

### Decision 2: Graceful degradation

**Choice:** `SoundManager.__init__()` wraps `pygame.mixer.init()` and
`pygame.mixer.Sound()` calls in try/except. If initialization fails (e.g.,
headless environment, missing file), the manager sets `self._available = False`
and all `play_*` methods become no-ops.

**Rationale:** The game must not crash when audio hardware is unavailable. In
CI/test environments there is typically no audio device.

### Decision 3: Double jump physics

**Choice:**
- `MAX_JUMPS = 2` — the character can jump at most twice while airborne.
- `DOUBLE_JUMP_VELOCITY = -10.0` — an additional upward velocity boost applied
  on the second jump (while in the air).
- `MarioCharacter._jump_count` tracks jumps since last landing; resets to 0 when
  `_jump_offset >= 0` (character returns to ground).
- First jump: `self._vy = JUMP_VELOCITY` (existing behavior, `-14.0`).
- Second jump: `self._vy += DOUBLE_JUMP_VELOCITY` (adds `-10.0` to current
  velocity, giving a second upward kick).

**Rationale:** Adding velocity (rather than replacing it) means the double jump
is most effective when used near the apex of the first jump, matching
platformer conventions. The `MAX_JUMPS = 2` cap ensures the character cannot
climb indefinitely off the top of the screen.

### Decision 4: Sound trigger points

**Choice:**
- **Coin sound:** Triggered in `MarioGameEngine._update_playing()` when
  `self._obstacle_manager.passed_count` increases after
  `self._obstacle_manager.update()`. The engine tracks the previous
  `passed_count` and compares.
- **Game-over sound:** Triggered in `_update_playing()` when a collision is
  detected and `self._state` transitions to `GAME_OVER`.

**Rationale:** The engine is the orchestrator of game state transitions, so it
is the natural place to fire sound events. The `ObstacleManager` remains
concerned only with obstacle logic.

### Decision 5: SoundManager lifecycle

**Choice:** `MarioGameEngine.__init__()` accepts an optional
`sound_manager: Optional[SoundManager] = None` parameter. If `None`, the engine
creates a default `SoundManager`. The engine's `reset()` method does not
destroy the sound manager — it persists across game restarts.

**Rationale:** Allows tests to inject a mock `SoundManager` and avoids
reloading sound files on every game restart.

## Risks / Trade-offs

- **[Risk] Double jump may make the game too easy.**
  → Mitigation: `DOUBLE_JUMP_VELOCITY` is tuned to be a modest boost; the
  `MAX_JUMPS = 2` cap and existing `JUMP_COOLDOWN` on the `JumpDetector`
  prevent spamming.

- **[Risk] `pygame.mixer` may not be available in all environments.**
  → Mitigation: Graceful degradation — if `pygame.mixer` fails to initialize,
  the `SoundManager` becomes a no-op and the game runs without sound.

- **[Risk] Sound files may not exist at runtime.**
  → Mitigation: `SoundManager` catches `FileNotFoundError` / `pygame.error`
  during loading and sets `_available = False`.

- **[Risk] Tests may fail in headless CI without audio devices.**
  → Mitigation: `SoundManager` tests use mocking or check the `_available` flag
  rather than requiring real audio hardware.

## Migration Plan

1. Create `src/sound_manager.py` with the `SoundManager` class.
2. Modify `src/mario_game.py`:
   - Add `MAX_JUMPS` and `DOUBLE_JUMP_VELOCITY` constants.
   - Modify `MarioCharacter.__init__()` to initialize `_jump_count`.
   - Modify `MarioCharacter.jump()` to support double jump.
   - Modify `MarioCharacter.update()` to reset `_jump_count` on landing.
   - Modify `MarioCharacter.reset()` to reset `_jump_count`.
   - Modify `MarioGameEngine.__init__()` to accept/create a `SoundManager`.
   - Modify `MarioGameEngine._update_playing()` to play sounds.
3. Modify `src/mario_main.py` to construct and pass a `SoundManager`.
4. Add `tests/test_sound_manager.py`.
5. Update `tests/test_mario_game.py` with double-jump and sound tests.
6. Update `README.md` with double-jump and sound documentation.

Rollback: Remove the `SoundManager` parameter from `MarioGameEngine`, revert
`MarioCharacter.jump()` to the original single-jump logic, and delete
`src/sound_manager.py` and `tests/test_sound_manager.py`.

## Open Questions

- Whether to also add double jump to the base game and Minecraft variant.
  → Decision: No — the user's request is scoped to the Mario game. Can be
  extended later if desired.
