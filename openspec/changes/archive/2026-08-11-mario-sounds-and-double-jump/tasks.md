## 1. Create SoundManager module

- [x] 1.1 Create `src/sound_manager.py` with `SoundManager` class
- [x] 1.2 Implement `pygame.mixer` initialization with graceful fallback
- [x] 1.3 Implement `play_coin()` and `play_game_over()` methods
- [x] 1.4 Implement `stop()` and `close()` cleanup methods

## 2. Add double jump to MarioCharacter

- [x] 2.1 Add `MAX_JUMPS = 2` and `DOUBLE_JUMP_VELOCITY` constants to `mario_game.py`
- [x] 2.2 Add `_jump_count` field to `MarioCharacter.__init__()`
- [x] 2.3 Modify `MarioCharacter.jump()` to allow second jump while airborne
- [x] 2.4 Modify `MarioCharacter.update()` to reset `_jump_count` on landing
- [x] 2.5 Modify `MarioCharacter.reset()` to reset `_jump_count`

## 3. Integrate sounds into MarioGameEngine

- [x] 3.1 Add `sound_manager` parameter to `MarioGameEngine.__init__()`
- [x] 3.2 Play coin sound when `passed_count` increases in `_update_playing()`
- [x] 3.3 Play game-over sound on collision in `_update_playing()`
- [x] 3.4 Add `close()` method to clean up sound manager

## 4. Update entry point

- [x] 4.1 Update `src/mario_main.py` to construct `SoundManager` and pass to engine
- [x] 4.2 Add cleanup in `finally` block

## 5. Tests

- [x] 5.1 Create `tests/test_sound_manager.py`
- [x] 5.2 Add double-jump tests to `tests/test_mario_game.py`
- [x] 5.3 Add sound integration tests to `tests/test_mario_game.py`
- [x] 5.4 Update existing `test_jump_fails_when_airborne` test to reflect double-jump behavior

## 6. Documentation

- [x] 6.1 Update `README.md` with double-jump and sound controls
- [x] 6.2 Update module docstrings in `src/mario_game.py`

## 7. Verification

- [x] 7.1 Run `pytest tests/test_sound_manager.py -v` — all pass
- [x] 7.2 Run `pytest tests/test_mario_game.py -v` — all pass
- [x] 7.3 Run `pytest tests/ -v` — full suite passes, no regressions
- [x] 7.4 Run `openspec validate --change mario-sounds-and-double-jump`
