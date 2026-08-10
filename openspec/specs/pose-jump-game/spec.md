# pose-jump-game Specification

## Purpose

An endless jumping game controlled by body pose detected from a Linux Ubuntu
webcam. A small character ("miniatura") rendered at the bottom of the screen
must jump over an endless stream of obstacles. The player jumps by physically
raising above a baseline height. Every 10 obstacles cleared, the game speed
increases. The game ends when the character collides with an obstacle.

## Requirements

### Requirement: Game startup and camera capture

The system SHALL open the webcam and display a menu screen waiting for input.

#### Scenario: Menu screen displayed

- **WHEN** the game starts and the camera is opened
- **THEN** the system renders a solid black screen with the text
  "POSE JUMP GAME — Press SPACE to start"
- **AND** no obstacles are spawned until the game starts

#### Scenario: Game starts on SPACE

- **WHEN** the application is in MENU state and the user presses SPACE
- **THEN** the system transitions to PLAYING state
- **AND** the character appears at ground level
- **AND** obstacles begin spawning from the right edge

### Requirement: Pose-based jump detection

The system SHALL detect a player jump from body pose landmarks and trigger the
character to jump.

#### Scenario: Player physically jumps

- **WHEN** the player raises their shoulders above the baseline by at least 50
  pixels in the camera feed
- **THEN** the system triggers a jump for the on-screen character
- **AND** the character applies upward velocity and leaves the ground
- **AND** gravity pulls the character back to ground level

#### Scenario: No false jump when standing

- **WHEN** the player is standing still or moving slightly within pose noise
- **THEN** the jump detector does not trigger
- **AND** the character remains on the ground

#### Scenario: Shoulders not visible

- **WHEN** landmarks 11 or 12 (shoulders) are not detected (occluded or out
  of frame)
- **THEN** the jump detector returns no jump event
- **AND** no ghost jumps are triggered

### Requirement: Miniatura character rendering

The system SHALL render the player's pose as a small stick-figure character
at a fixed horizontal position, using a solid black background with no camera
feed.

#### Scenario: Character rendered as head circle + body lines

- **WHEN** the player is detected
- **THEN** the system renders a head circle at the nose landmark position and
  body lines connecting landmarks with index >= 11 (no face connections)
- **AND** the character is rendered at a fixed x position (80 px from left)
  near the bottom of the screen
- **AND** the pose landmarks are scaled to approximately 90 px height

#### Scenario: Character jumps on screen

- **WHEN** a jump is triggered
- **THEN** the entire miniatura moves upward with physics (velocity + gravity)
- **AND** returns to ground level when landing

### Requirement: Obstacle spawning and movement

The system SHALL spawn rectangular obstacles from the right edge of the screen
that move leftward at the current game speed.

#### Scenario: Obstacle appears at right edge

- **WHEN** the game is PLAYING
- **THEN** obstacles spawn at the right edge of the screen (x = width)
- **AND** each obstacle has a width of 30 px and a randomly selected height

#### Scenario: Obstacles move leftward

- **WHEN** an obstacle is spawned
- **THEN** it moves leftward each frame at the current game speed
- **AND** when it moves completely off the left edge (x + width < 0), it is
  removed from the game

#### Scenario: Obstacle spawn timing

- **WHEN** the time since the last obstacle spawn exceeds a random interval
  in the range 40–90 frames
- **THEN** a new obstacle spawns at the right edge

### Requirement: Speed progression

The system SHALL increase the game speed every 10 obstacles successfully
passed.

#### Scenario: Speed increases after 10 obstacles

- **WHEN** the player has passed 10 obstacles without collision
- **THEN** the game speed is multiplied by 1.10
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

#### Scenario: Speed at 20 passed obstacles

- **WHEN** the player has passed 20 obstacles without collision
- **THEN** the game speed is `BASE_SPEED * 1.10^2`

### Requirement: Collision and game over

The system SHALL detect collisions between the character and obstacles and end
the game on impact.

#### Scenario: Character hits obstacle

- **WHEN** the character's bounding box overlaps an obstacle's bounding box
- **THEN** the system transitions to GAME_OVER state
- **AND** the game stops spawning and moving obstacles
- **AND** the final score (obstacles passed) is displayed

#### Scenario: Obstacle passed without collision

- **WHEN** an obstacle's right edge moves past the character's x position
  without collision
- **THEN** the passed-obstacle counter increments by 1

### Requirement: Game states and restart

The system SHALL support three game states: MENU, PLAYING, and GAME_OVER.

#### Scenario: Game over screen displayed

- **WHEN** the character collides with an obstacle
- **THEN** the system displays "GAME OVER — Score: N" and the speed multiplier
- **AND** the system waits for SPACE to be pressed

#### Scenario: Restart from game over

- **WHEN** the system is in GAME_OVER state and the user presses SPACE
- **THEN** the system resets all game state (score, speed, player position,
  obstacles, jump baseline) and transitions to PLAYING

#### Scenario: Quit the game

- **WHEN** the application window is focused and the user presses `q` or ESC
- **THEN** the system closes all windows, releases the camera, and exits

### Requirement: HUD display

The system SHALL display on-screen information during gameplay.

#### Scenario: Score and speed shown during play

- **WHEN** the game is PLAYING
- **THEN** the system overlays the current score (obstacles passed) and the
  current speed multiplier on the frame
