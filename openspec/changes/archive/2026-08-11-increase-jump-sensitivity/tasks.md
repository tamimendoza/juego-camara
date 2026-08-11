## 1. Update Constants

- [x] 1.1 Set `JUMP_THRESHOLD` from 50.0 to 30.0 in `src/game.py`
- [x] 1.2 Set `JUMP_COOLDOWN` from 15 to 8 in `src/game.py`
- [x] 1.3 Set `JUMP_VELOCITY` from -11.0 to -14.0 in `src/game.py`
- [x] 1.4 Set `GRAVITY` from 0.5 to 0.45 in `src/game.py`

## 2. Update Tests

- [x] 2.1 Update `JumpDetector` test assertions that hard-code threshold=50 / cooldown=15 to use the new values (or rely on defaults)
- [x] 2.2 Add a test verifying the character's jump apex height exceeds the maximum obstacle height (120 px)
- [x] 2.3 Update `test_no_jump_when_shoulders_rise_below_threshold` to reflect the 30 px threshold

## 3. Verification

- [x] 3.1 Run `pytest tests/test_game.py` — all tests pass
- [x] 3.2 Run `openspec validate --change increase-jump-sensitivity` — no schema errors
