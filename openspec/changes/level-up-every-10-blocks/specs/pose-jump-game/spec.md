## ADDED Requirements

### Requirement: Level progression

The system SHALL increment the player's level every 10 obstacles successfully
passed. Level 1 covers 0–9 obstacles, level 2 covers 10–19, level 3 covers
20–29, and so on.

#### Scenario: Level 1 at game start

- **WHEN** the game starts (PLAYING state) with 0 obstacles passed
- **THEN** the player is at level 1

#### Scenario: Level 2 after 10 obstacles

- **WHEN** the player has passed 10 obstacles without collision
- **THEN** the player's level increments to 2

#### Scenario: Level increases with block count

- **WHEN** the player has passed 20, 30, 40 obstacles without collision
- **THEN** levels advance to 3, 4, 5 respectively

## MODIFIED Requirements

### Requirement: Speed progression

The system SHALL increase the game speed from level 2 onward, ramping gradually
with each level. Speed is computed as `BASE_SPEED * SPEED_MULTIPLIER^(level - 1)`.
At level 1 (0–9 obstacles) speed remains at `BASE_SPEED`. At level 2 (10–19
obstacles) speed is multiplied by 1.10. Each subsequent level applies another
1.10 multiplier.

#### Scenario: Speed increases after level 2

- **WHEN** the player reaches level 2 (10 obstacles passed) without collision
- **THEN** the game speed is `BASE_SPEED * 1.10`
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

#### Scenario: Speed at 20 passed obstacles

- **WHEN** the player has passed 20 obstacles without collision (level 3)
- **THEN** the game speed is `BASE_SPEED * 1.10^2`

### Requirement: HUD display

The system SHALL display on-screen information during gameplay.

#### Scenario: Score, level, and speed shown during play

- **WHEN** the game is PLAYING
- **THEN** the system overlays the current level, score (obstacles passed), and
  the current speed multiplier on the frame

#### Scenario: Level shown on game over

- **WHEN** the game transitions to GAME_OVER state
- **THEN** the system displays the final level alongside the score and speed
  multiplier on the game over screen