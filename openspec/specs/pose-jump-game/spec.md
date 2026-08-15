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
character to jump, but only when the player first bends their legs and then
performs an actual jump. Raising the shoulders alone must never trigger a jump.

#### Scenario: Player physically jumps

- **WHEN** the player bends both legs (crouches) and then performs an actual
  jump so the body rises at least 30 pixels above the crouch baseline in the
  camera feed
- **THEN** the system triggers a jump for the on-screen character
- **AND** the character applies upward velocity and leaves the ground
- **AND** gravity pulls the character back to ground level

#### Scenario: No jump from shoulders alone

- **WHEN** the player raises their shoulders by 30 pixels or more but never
  bends their legs
- **THEN** the jump detector does not trigger
- **AND** the character remains on the ground

#### Scenario: No false jump when standing

- **WHEN** the player is standing still or moving slightly within pose noise
- **THEN** the jump detector does not trigger
- **AND** the character remains on the ground

#### Scenario: Crouching without jumping does not fire

- **WHEN** the player bends their legs (crouches) but stands back up without
  jumping
- **THEN** no jump is triggered after the crouch expires
- **AND** the character remains on the ground

#### Scenario: Shoulders not visible

- **WHEN** the shoulders or the legs (knees/ankles) are not detected
  (occluded or out of frame)
- **THEN** the jump detector returns no jump event
- **AND** no ghost jumps are triggered

#### Scenario: Rapid re-jump after landing

- **WHEN** the player lands and then bends their legs and jumps again within a
  short period
- **THEN** the system SHALL trigger a second jump without requiring the full
  previous cooldown to elapse
- **AND** the cooldown between allowed jump triggers is no more than 8 frames

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
- **THEN** the system overlays the current level, score (obstacles passed), and
  the current speed multiplier on the frame

#### Scenario: Level shown on game over

- **WHEN** the game transitions to GAME_OVER state
- **THEN** the system displays the final level alongside the score and speed
  multiplier on the game over screen

### Requirement: Jump clears all obstacle heights

The system SHALL give the miniatura character enough vertical clearance during
a jump to pass over every possible obstacle height without colliding.

#### Scenario: Character clears the tallest obstacle

- **WHEN** the player executes a successful jump (shoulders rise above baseline)
- **THEN** the character's jump apex is at least 20 pixels higher than the
  maximum obstacle height (120 px)
- **AND** the character lands back on the ground without colliding with the
  obstacle

#### Scenario: Jump sensitivity enables timely obstacle clearance

- **WHEN** an obstacle approaches the character and the player initiates a
  jump with a small shoulder movement (at least 30 px)
- **THEN** the jump is triggered with sufficient sensitivity that the character
  clears the obstacle before the character's bounding box overlaps the
  obstacle's bounding box

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

### Requirement: Character torso rendered solid

The system SHALL render the miniatura character's torso as a filled solid
region instead of an empty outline, so the chest does not look hollow.

#### Scenario: Torso filled with character color

- **WHEN** the character is rendered with a detected pose
- **THEN** the torso quadrilateral (between the shoulders and the hips) is
  filled with a solid color matching the character's own color
- **AND** the head circle and body lines continue to render on top as before

### Requirement: Character stays inside the visible area during jumps

The system SHALL keep the whole character inside the visible game area at all
times, including during jumps and double jumps.

#### Scenario: Jump does not leave the top of the screen

- **WHEN** the character jumps and reaches its highest point (including a
  double jump)
- **THEN** the entire character remains fully inside the visible area
- **AND** no part of the character (head, arms, or legs) is clipped off the
  top of the screen

#### Scenario: Jump still clears every obstacle height

- **WHEN** the character jumps with the height capped to stay on screen
- **THEN** the jump apex is still at least 20 pixels higher than the tallest
  obstacle, so every obstacle can be cleared

