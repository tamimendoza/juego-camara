# mario-face-jump-rules Delta Specification

## MODIFIED Requirements

### Requirement: Additive speed multiplier

**RENAMED to:** Multiplicative speed multiplier

The system SHALL increase the game speed by a factor of 2.0 per level, applied
multiplicatively. Speed is computed as `BASE_SPEED * SPEED_MULTIPLIER^(level - 1)`
with `SPEED_MULTIPLIER = 2.0`. At level 1 the multiplier is 1.0, at level 2 it is
2.0, at level 3 it is 4.0, and so on — the game becomes twice as fast per level.

#### Scenario: Speed multiplier at level 1

- **WHEN** the player is at level 1
- **THEN** the speed multiplier is 1.0
- **AND** the game speed is `BASE_SPEED`

#### Scenario: Speed multiplier at level 2

- **WHEN** the player reaches level 2 (5 obstacles passed)
- **THEN** the speed multiplier is 2.0
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

#### Scenario: Speed multiplier at level 3

- **WHEN** the player reaches level 3 (10 obstacles passed)
- **THEN** the speed multiplier is 4.0
