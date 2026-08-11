## Why

The Mario Bros game variant currently has no audio feedback and only supports a
single jump per airborne cycle. Two enhancements are requested:

1. **Sound effects** — The `sounds/` directory contains two Mario-themed audio
   files (`mario-moneda.mp3` for coin collection and `mario-bros-game-over-1.mp3`
   for game over). These should play at the appropriate moments: the coin sound
   when the player successfully clears an obstacle by jumping, and the game-over
   sound when the character collides with an obstacle.

2. **Double jump** — The character should be able to perform a second jump while
   airborne, reaching a higher apex. However, a maximum of 2 jumps is enforced so
   the character cannot climb off the top of the screen.

## What Changes

- **Add a `SoundManager` class** (`src/sound_manager.py`) using `pygame.mixer`
  (already a project dependency) to load and play the two MP3 files from the
  `sounds/` directory. The manager degrades gracefully when audio is
  unavailable (headless environments, missing files).

- **Add double-jump logic to `MarioCharacter`** (`src/mario_game.py`):
  - Track `_jump_count` (jumps performed since last landing).
  - `jump()` allows a second call while airborne, applying an additional upward
    velocity boost (`DOUBLE_JUMP_VELOCITY`).
  - A `MAX_JUMPS = 2` cap prevents a third jump.
  - `_jump_count` resets to 0 when the character returns to the ground.

- **Integrate sound playback into `MarioGameEngine`**:
  - Play the coin sound when an obstacle is marked as passed.
  - Play the game-over sound when a collision transitions the game to
    `GAME_OVER`.

- **Update `src/mario_main.py`** to construct a `SoundManager` and pass it to
  the `MarioGameEngine`.

- **Add tests** in `tests/test_mario_game.py` for double-jump physics and
  sound integration, and `tests/test_sound_manager.py` for the `SoundManager`
  class.

## Capabilities

### New Capabilities

- `mario-sounds`: Audio feedback (coin sound on obstacle clearance, game-over
  sound on collision) in the Mario Bros game variant.
- `mario-double-jump`: The Mario character can perform a second jump while
  airborne for extra height, capped at 2 total jumps per airtime.

### Modified Capabilities

- `mario-bros-variant`: `MarioCharacter.jump()` gains double-jump support;
  `MarioGameEngine` gains sound integration points.

## Impact

- **New**: `src/sound_manager.py` — `SoundManager` class for loading and playing
  MP3 sound effects via `pygame.mixer`.
- **Modified**: `src/mario_game.py` — `MarioCharacter` gains double-jump fields
  and logic; `MarioGameEngine` gains a `SoundManager` and plays sounds on
  obstacle pass and game over.
- **Modified**: `src/mario_main.py` — constructs `SoundManager` and passes to
  engine.
- **New**: `tests/test_sound_manager.py` — unit tests for `SoundManager`.
- **Modified**: `tests/test_mario_game.py` — adds double-jump and sound tests.
- **Modified**: `README.md` — documents double-jump and sound controls.
