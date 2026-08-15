## MODIFIED Requirements

### Requirement: Speed progression

The system SHALL increase the game speed from level 2 onward, ramping gradually with each level. Speed is computed as `BASE_SPEED * SPEED_MULTIPLIER^(level - 1)`.

At level 1 (0–9 obstacles) speed remains at `BASE_SPEED`. At level 2 (10–19 obstacles) speed is multiplied by **2.0**. Each subsequent level applies another **2.0** multiplier.

#### Scenario: Speed increases after 10 obstacles

- **WHEN** the player reaches level 2 (10 obstacles passed) without collision
- **THEN** the game speed is `BASE_SPEED * SPEED_MULTIPLIER^(level - 1)` = `BASE_SPEED * 2.0`
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

#### Scenario: Speed at 20 passed obstacles

- **WHEN** the player has passed 20 obstacles without collision (level 3)
- **THEN** the game speed is `BASE_SPEED * 2.0^2`
