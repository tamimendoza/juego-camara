## Context

See proposal.md — Why. The relevant code is in `src/game.py`:

```
JUMP_THRESHOLD = 50.0   # px shoulder rise to trigger
JUMP_COOLDOWN  = 15     # frames between allowed triggers
GRAVITY        = 0.5    # px/frame²
JUMP_VELOCITY  = -11.0  # initial upward velocity

# Max jump height = v² / (2·g) = 121 / 1.0 = 121 px
# Tallest obstacle = 120 px → barely cleared
```

`JumpDetector` uses `JUMP_THRESHOLD`/`JUMP_COOLDOWN` as constructor defaults; `PlayerCharacter.jump()` uses `JUMP_VELOCITY` and the physics loop applies `GRAVITY`. Existing tests in `tests/test_game.py` reference `JUMP_THRESHOLD`, `JUMP_COOLDOWN`, and the physics values directly.

## Goals / Non-Goals

**Goals:**
- Reduce jump trigger threshold to 30 px and cooldown to 8 frames
- Give the character enough vertical clearance (apex ≥ 140 px) to clear the tallest obstacle (120 px) with margin
- Keep all existing jump/physics tests passing by updating value-dependent assertions

**Non-Goals:**
- Changing obstacle spawn timing, heights, or game speed
- Adding double-jump or mid-air control
- Modifying pose detection or landmark extraction

## Decisions

### Decision 1: Tune constants for sensitivity and clearance

**Choice:** Set `JUMP_THRESHOLD = 30.0`, `JUMP_COOLDOWN = 8`, `JUMP_VELOCITY = -14.0`, `GRAVITY = 0.45`.

**Rationale:**
- 30 px threshold means a small, natural shoulder rise triggers a jump — sensitive enough to react in time for close obstacles.
- 8-frame cooldown (at ~30 FPS) lets the player re-jump ~0.27 s after landing, enabling tight sequences.
- New max jump height = `-14.0² / (2·0.6) = 196 / 1.2 ≈ 163 px` (discrete simulation ≈ 156 px) — well above the 120 px max obstacle, giving ample clearance margin while reducing air-time for a faster fall.

| Constant      | Old  | New   | Effect                              |
|---------------|------|-------|-------------------------------------|
| JUMP_THRESHOLD| 50.0 | 30.0  | Smaller movement triggers jump      |
| JUMP_COOLDOWN | 15   | 8     | Faster re-jump after landing        |
| JUMP_VELOCITY | -11.0| -14.0 | Higher apex (~156 px vs ~121 px)     |
| GRAVITY       | 0.5  | 0.6   | Faster fall / shorter air-time      |

**Alternatives considered:**
- Only lowering threshold, not velocity: detection improves but the character still can't clear tall obstacles — doesn't fully solve "no deja pasar los obstáculos".
- Increasing velocity without lowering threshold: jump is higher but detection stays sluggish — misses the "more sensitive" requirement.

### Decision 2: Update constants in place (no API change)

**Choice:** Modify the module-level constants in `src/game.py` and keep the same constructor signatures for `JumpDetector` and `PlayerCharacter`.

**Rationale:** The constants are already the single source of truth and are referenced by tests. Changing the constants propagates to the defaults everywhere without any API surface change.

## Risks / Trade-offs

- **[Risk] Too-sensitive detection causes accidental jumps from pose jitter.** → Mitigation: the 30 px threshold still requires meaningful shoulder elevation; the EMA baseline continues to smooth position. If false positives appear in playtesting, the threshold can be nudged up to 35.
- **[Risk] Higher jump makes the game too easy.** → Trade-off accepted: the speed progression (×1.10 per 10 obstacles) still ramps up difficulty; the primary complaint is that obstacles can't be passed at all.

## Migration Plan

This is a pure constant-tuning change. No data migration, no API changes, no config files. The change applies instantly on redeployment. Rollback is reverting the four constant values.

## Open Questions

*(none)*
