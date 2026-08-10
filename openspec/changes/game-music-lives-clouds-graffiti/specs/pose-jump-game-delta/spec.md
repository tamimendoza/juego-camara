## Purpose

Delta for the existing pose-jump-game spec: level interval changes from 10 to 5,
plus new requirements for lives, sky blocks, clouds, ground, graffiti, music,
invincibility theme, and pose stability.

## MODIFIED Requirements

### Requirement: Speed progression

The system SHALL increase the game speed every 5 obstacles successfully passed
(was 10).

#### Scenario: Speed increases after 5 obstacles

- **WHEN** the player has passed 5 obstacles without collision
- **THEN** the game speed is multiplied by 1.10
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

#### Scenario: Speed at 10 passed obstacles

- **WHEN** the player has passed 10 obstacles without collision
- **THEN** the game speed is `BASE_SPEED * 1.10^2`

### Requirement: Collision and game over

The system SHALL detect collisions between the character and obstacles and end
the game on impact.

#### Scenario: Character hits obstacle

- **WHEN** the character's bounding box overlaps an obstacle's bounding box
- **THEN** the system decrements the life count by 1
- **AND** if lives remain, the game continues
- **AND** if lives reach 0, the system transitions to GAME_OVER state

#### Scenario: Obstacle passed without collision

- **WHEN** an obstacle's right edge moves past the character's x position
  without collision
- **THEN** the passed-obstacle counter increments by 1
- **AND** the coin sound plays
- **AND** obstacles already marked as passed do NOT trigger collision detection

### Requirement: Game states and restart

The system SHALL support three game states: MENU, PLAYING, and GAME_OVER.

#### Scenario: Game over screen displayed

- **WHEN** the character has 0 lives remaining and collides with an obstacle
- **THEN** the system displays "GAME OVER — Score: N" and the speed multiplier
- **AND** the system waits for SPACE to be pressed

#### Scenario: Restart from game over

- **WHEN** the system is in GAME_OVER state and the user presses SPACE
- **THEN** the system resets all game state (score, speed, player position,
  obstacles, jump baseline, lives) and transitions to PLAYING

## ADDED Requirements

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
