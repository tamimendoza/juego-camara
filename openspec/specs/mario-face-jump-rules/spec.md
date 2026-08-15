# mario-face-jump-rules Specification

## Purpose
Defines the gameplay rules of the Mario Face Jump variant: level progression every
5 obstacles, coin accumulation from obstacles passed, lives restored by sky squares,
and an additive speed multiplier that increases by 0.1 per level.
## Requirements
### Requirement: Level up every 5 obstacles

The system SHALL increment the player's level by 1 every 5 obstacles successfully
passed. Level 1 covers obstacles 1–5, level 2 covers 6–10, level 3 covers 11–15,
and so on.

#### Scenario: Level 1 at game start

- **WHEN** the game starts (PLAYING state) with 0 obstacles passed
- **THEN** the player is at level 1

#### Scenario: Level 2 after 5 obstacles

- **WHEN** the player has passed 5 obstacles without collision
- **THEN** the player's level increments to 2

#### Scenario: Level increases every 5 obstacles

- **WHEN** the player has passed 10, 15, 20 obstacles without collision
- **THEN** levels advance to 3, 4, 5 respectively

### Requirement: Coin per obstacle passed

The system SHALL grant 1 coin for every obstacle successfully passed by the
character, independent of sky squares.

#### Scenario: Coin awarded for passing an obstacle

- **WHEN** the character passes an obstacle without collision
- **THEN** the coin counter increments by 1
- **AND** a coin sound effect plays

#### Scenario: Coin counter accumulates obstacles passed

- **WHEN** the character passes obstacles during a game
- **THEN** the coin counter accumulates 1 coin per obstacle passed

### Requirement: Multiplicative speed multiplier

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

### Requirement: Everything advances with speed

The system SHALL scale the movement of obstacles, clouds, and sky squares with the
current game speed, so that when the speed increases all of them advance faster.

#### Scenario: Obstacles, clouds, and sky squares speed up together

- **WHEN** the game speed increases due to a level up
- **THEN** obstacles, clouds, and sky squares all move leftward faster in
  proportion to the new speed
- **AND** the parallax relationship between clouds and obstacles is preserved

### Requirement: Sky rendered light sky-blue

The system SHALL render the game sky in a light sky-blue (celeste) color during
gameplay.

#### Scenario: Playing state shows celeste sky

- **WHEN** the game is in PLAYING state
- **THEN** the frame background is filled with light sky-blue (celeste)
- **AND** clouds, sky squares, obstacles, and the character are drawn on top of it

