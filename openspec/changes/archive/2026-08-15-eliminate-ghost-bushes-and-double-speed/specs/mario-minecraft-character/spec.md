# mario-minecraft-character Delta Specification

## MODIFIED Requirements

### Requirement: Speed progression

The system SHALL increase the game speed by a factor of 2.0 per level, applied
multiplicatively. Speed is computed as `BASE_SPEED * SPEED_MULTIPLIER^(level - 1)`
with `SPEED_MULTIPLIER = 2.0`.

#### Scenario: Speed increases after 10 obstacles

- **WHEN** the player has passed 10 obstacles without collision
- **THEN** the game speed is multiplied by 2.0
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed
