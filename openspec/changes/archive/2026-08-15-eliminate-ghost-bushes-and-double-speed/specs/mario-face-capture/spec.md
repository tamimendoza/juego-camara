# mario-face-capture Delta Specification

## MODIFIED Requirements

### Requirement: Speed progression

The system SHALL increase the game speed by a factor of 2.0 per level, applied
multiplicatively, matching the base Mario game. Speed is computed as
`BASE_SPEED * SPEED_MULTIPLIER^(level - 1)` with `SPEED_MULTIPLIER = 2.0`.

#### Scenario: Speed increases after 5 obstacles

- **WHEN** the player has passed 5 obstacles without collision (level 2)
- **THEN** the game speed is multiplied by 2.0
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

#### Scenario: Speed increases after 10 obstacles

- **WHEN** the player has passed 10 obstacles without collision (level 3)
- **THEN** the game speed is multiplied by 4.0 (2.0²)
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed
