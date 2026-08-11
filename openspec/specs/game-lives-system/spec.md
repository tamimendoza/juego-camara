# game-lives-system Specification

## Purpose
A lives system where the character starts with 3 lives, rendered as 3 hearts in
the HUD. Each obstacle collision costs one life. The game ends when all lives are
lost.
## Requirements
### Requirement: Three lives as visible hearts

The system SHALL display 3 hearts in the HUD, one for each life.

#### Scenario: Three hearts shown at game start

- **WHEN** the game is in PLAYING state
- **THEN** the system renders 3 hearts in the top-left HUD area
- **AND** all 3 hearts are fully visible (not dimmed)

### Requirement: Collision costs a life

The system SHALL decrement the life count by 1 when the character collides with an
obstacle.

#### Scenario: Heart disappears on collision

- **WHEN** the character collides with an obstacle
- **THEN** one heart disappears from the HUD (life count decreases by 1)
- **AND** the game continues (does not end) if lives remain

#### Scenario: Game over at zero lives

- **WHEN** the character has 0 lives remaining and collides with an obstacle
- **THEN** the system transitions to GAME_OVER state
- **AND** a game-over sound plays

### Requirement: Lives reset on restart

The system SHALL restore all 3 lives when the game restarts from GAME_OVER.

#### Scenario: Hearts restored on restart

- **WHEN** the player presses SPACE from GAME_OVER state
- **THEN** the life count resets to 3
- **AND** all 3 hearts are visible again

