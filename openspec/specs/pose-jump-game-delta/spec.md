# pose-jump-game-delta Specification

## Purpose
Delta for the existing pose-jump-game spec: level interval changes from 10 to 5,
plus new requirements for lives, sky blocks, clouds, ground, graffiti, music,
invincibility theme, and pose stability.
## Requirements
### Requirement: Level progression at 5 obstacles

The system SHALL increment the level every 5 obstacles successfully passed.

#### Scenario: Level up at 5 obstacles

- **WHEN** the player has passed 5 obstacles without collision
- **THEN** the level increments to 2
- **AND** the game speed increases by 10%
- **AND** a "LEVEL UP" overlay is displayed

#### Scenario: Level up at 10 obstacles

- **WHEN** the player has passed 10 obstacles without collision
- **THEN** the level increments to 3
- **AND** the game speed increases by 10% again (cumulative)

### Requirement: Lives system

The system SHALL implement a 3-life system with visible hearts.

#### Scenario: Three hearts shown during play

- **WHEN** the game is in PLAYING state
- **THEN** the system renders 3 hearts in the HUD
- **AND** hearts disappear as lives are lost

### Requirement: Sky blocks

The system SHALL render square blocks in the sky that grant lives when touched.

#### Scenario: Sky block grants life on touch

- **WHEN** the character's bounding box overlaps a sky block during a jump
- **THEN** the system increments the life count by 1 (capped at 3)
- **AND** the block disappears
- **AND** a coin sound effect plays

### Requirement: Moving clouds

The system SHALL animate clouds to drift leftward to simulate forward motion.

#### Scenario: Clouds drift across sky

- **WHEN** the game is in PLAYING state
- **THEN** clouds move leftward at a constant drift speed
- **AND** clouds wrap around to the right edge when they move off the left

### Requirement: Brick ground with graffiti

The system SHALL render a brick-colored ground with graffiti text.

#### Scenario: Ground has brick color and pattern

- **WHEN** the game is in PLAYING state
- **THEN** the ground is filled with a brick color
- **AND** a brick pattern is drawn across the ground area
- **AND** the text "Familia Mendoza Silva" is drawn as graffiti on the ground

### Requirement: Background music

The system SHALL play GroundTheme.mp3 as continuous background music during
gameplay.

#### Scenario: Music plays during gameplay

- **WHEN** the game is in PLAYING state
- **THEN** the system plays GroundTheme.mp3 on a continuous loop
- **AND** the music volume is below sound-effect volume levels

### Requirement: Invincibility theme

The system SHALL play InvincibilityTheme.mp3 when the player has 5 or more coins.

#### Scenario: Theme starts at 5 coins

- **WHEN** the player's score reaches 5
- **THEN** the system plays InvincibilityTheme.mp3 layered on top of the
  background music

### Requirement: Pose stability

The system SHALL pause the game and display a warning when pose detection
degrades.

#### Scenario: Warning displayed when detection is poor

- **WHEN** pose detection quality is poor (too few landmarks or out-of-range
  shoulder width)
- **THEN** the system pauses the game
- **AND** displays "Acerquese o alejese de la camara" at the top of the screen
- **AND** the character remains still in its last known pose

