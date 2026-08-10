## ADDED Requirements

### Requirement: Sound effects

The system SHALL play sound effects at specific game events using the audio
files in the `sounds/` directory.

#### Scenario: Coin sound plays when obstacle is cleared

- **WHEN** the player's character jumps over an obstacle and the obstacle's
  right edge passes the character's x position
- **THEN** the system plays the coin sound (`sounds/mario-moneda.mp3`)
- **AND** the sound plays once per obstacle cleared (not on every frame)

#### Scenario: Game-over sound plays on collision

- **WHEN** the character's bounding box overlaps an obstacle's bounding box
- **THEN** the system transitions to GAME_OVER state
- **AND** the system plays the game-over sound
  (`sounds/mario-bros-game-over-1.mp3`)

#### Scenario: Game runs without audio hardware

- **WHEN** `pygame.mixer` cannot initialize (headless/CI environment)
- **THEN** the system does not crash
- **AND** all sound playback calls become no-ops

### Requirement: Double jump

The system SHALL allow the Mario character to perform a second jump while
airborne, reaching a higher apex, with a maximum of 2 jumps per airtime.

#### Scenario: First jump triggers normally

- **WHEN** the character is on the ground and a jump is detected
- **THEN** the character applies `JUMP_VELOCITY` upward and leaves the ground
- **AND** `_jump_count` is set to 1

#### Scenario: Second jump while airborne (double jump)

- **WHEN** the character is airborne (`_jump_count == 1`) and a jump is
  detected
- **THEN** the character applies an additional `DOUBLE_JUMP_VELOCITY` boost
- **AND** `_jump_count` is incremented to 2
- **AND** the character's apex is higher than a single jump

#### Scenario: Third jump is prevented

- **WHEN** the character is airborne (`_jump_count == 2`) and a jump is
  detected
- **THEN** `jump()` returns `False`
- **AND** no additional velocity is applied

#### Scenario: Jump count resets on landing

- **WHEN** the character returns to the ground (`_jump_offset >= 0`)
- **THEN** `_jump_count` is reset to 0
- **AND** `_on_ground` is set to `True`

## MODIFIED Requirements

### Requirement: Pose-based jump detection

The system SHALL detect a player jump from body pose landmarks and trigger the
character to jump.

#### Scenario: Double jump detected from second physical jump

- **WHEN** the player performs a second physical jump gesture while the
  character is still airborne
- **THEN** the system triggers a second jump for the on-screen character
- **AND** the character receives an additional upward velocity boost
- **AND** a third jump gesture while airborne does not trigger another jump
