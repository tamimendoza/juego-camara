## Why

The pose jump game's jump mechanic is not sensitive enough to reliably clear obstacles. With the current physics, the character's maximum jump height (~121 px at `JUMP_VELOCITY = -11.0` and `GRAVITY = 0.5`) barely exceeds the tallest obstacles (up to 120 px). Combined with a 50 px detection threshold and a 15-frame cooldown, players must make large, exaggerated jumps that are often too late to clear incoming obstacles — the character collides instead of passing over. Making the jump more sensitive lets players react faster and clear obstacles reliably with a smaller, more natural movement.

## What Changes

- **Lower the jump detection threshold** from 50 px to 30 px so smaller shoulder elevation triggers a jump sooner
- **Reduce the jump cooldown** from 15 frames to 8 frames so the player can re-trigger a jump more quickly when spacing is tight
- **Increase the initial jump velocity** from -11.0 to -14.0 so the character reaches a higher apex (~156 px) and clears the tallest obstacles with margin
- **Increase gravity** from 0.5 to 0.6 for a faster fall (shorter air-time) while keeping the apex (~156 px) well above the tallest obstacle (120 px)
- Update existing unit tests that hard-code the old threshold, cooldown, and velocity values
- Add a dedicated test verifying the new jump height exceeds the maximum obstacle height

## Capabilities

### New Capabilities
*(none)*

### Modified Capabilities
- `pose-jump-game`: The jump detection threshold, cooldown, and physics constants (velocity, gravity) are tuned to make jumping more sensitive and give the character enough clearance to clear all obstacle heights.

## Impact

- **Modified**: `src/game.py` — constants `JUMP_THRESHOLD`, `JUMP_COOLDOWN`, `JUMP_VELOCITY`, `GRAVITY` and the default arguments of `JumpDetector` and `PlayerCharacter`
- **Modified**: `tests/test_game.py` — update assertions that reference the old threshold/cooldown and add jump-height coverage
