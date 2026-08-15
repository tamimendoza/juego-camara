# mario-bros-variant Specification

## Purpose
A Mario Bros-themed variant of the pose-controlled jumping game. The player's
pose (detected via webcam) is rendered as a Mario-styled miniatura character
that must jump over scrolling Mario Bros obstacles (pipes, blocks, goombas).
Obstacles start widely separated so players can advance through levels, with
difficulty increasing progressively.
## Requirements
### Requirement: Game startup and camera capture

The Mario Bros game SHALL open the webcam and display a themed menu screen
waiting for input.

#### Scenario: Menu screen displayed

- **WHEN** the game starts and the camera is opened
- **THEN** the system renders a sky-blue background with drawn clouds, bushes,
  and a brick ground, overlaid with "MARIO POSE JUMP — Press SPACE to start"
- **AND** no obstacles are spawned until the game starts

#### Scenario: Game starts on SPACE

- **WHEN** the application is in MENU state and the user presses SPACE
- **THEN** the system transitions to PLAYING state
- **AND** the Mario character appears at ground level
- **AND** obstacles begin spawning from the right edge with wide gaps (level 1)

### Requirement: Pose-based jump detection

The system SHALL detect a player jump from body pose landmarks and trigger the
Mario character to jump, but only when the player first bends their legs and
then performs an actual jump. Raising the shoulders alone must never trigger a
jump.

#### Scenario: Player physically jumps

- **WHEN** the player bends both legs (crouches) and then performs an actual
  jump so the body rises at least 30 pixels above the crouch baseline in the
  camera feed
- **THEN** the system triggers a jump for the Mario character
- **AND** the character applies upward velocity and leaves the ground
- **AND** gravity pulls the character back to the ground level

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
- **THEN** the jump detector returns no jump event
- **AND** no ghost jumps are triggered

### Requirement: Mario character rendering

The system SHALL render the player's pose as a small Mario-styled character
at a fixed horizontal position, using a solid sky-blue background with no
camera feed.

#### Scenario: Character rendered with Mario palette

- **WHEN** the player is detected
- **THEN** the system renders a peach face circle at the nose landmark position
  with a red cap above it and brown hair arc
- **AND** the system draws body lines in Mario colours: red for arms/torso
  (shirt) and blue for legs (overalls)
- **AND** face connections (landmarks 0–10) are excluded
- **AND** the character is rendered at a fixed x position (80 px from left)
  near the bottom of the screen
- **AND** the pose landmarks are scaled to approximately 90 px height

#### Scenario: Character jumps on screen

- **WHEN** a jump is triggered
- **THEN** the entire Mario miniatura moves upward with physics (velocity +
  gravity)
- **AND** returns to the ground line when landing

### Requirement: Mario-themed background

The system SHALL render a Mario Bros-style background behind the character and
obstacles.

#### Scenario: Sky, clouds, bushes, and ground drawn

- **WHEN** the game is in PLAYING state
- **THEN** the system fills the frame with sky blue
- **AND** draws white fluffy clouds at fixed positions
- **AND** draws green bushes with red flowers near the ground
- **AND** draws a brown brick-patterned ground band at the bottom 15% of the
  screen

### Requirement: Obstacle spawning and movement

The system SHALL spawn Mario-themed obstacles (pipes, blocks, goombas) from the
right edge of the screen that move leftward at the current game speed.

#### Scenario: Obstacle appears at right edge

- **WHEN** the game is PLAYING
- **THEN** obstacles spawn at the right edge of the screen (x = width)
- **AND** each obstacle is one of three types: pipe (green, 40×80), block
  (orange, 40×40), or goomba (red-brown, 30×30)
- **AND** obstacle types cycle sequentially (pipe → block → goomba → pipe ...)

#### Scenario: Obstacles move leftward

- **WHEN** an obstacle is spawned
- **THEN** it moves leftward each frame at the current game speed
- **AND** when it moves completely off the left edge (x + width < 0), it is
  removed from the game

#### Scenario: Wide obstacle spacing at level 1

- **WHEN** the player is at level 1 (0 obstacles passed)
- **THEN** obstacles spawn at intervals of 150–250 frames
- **AND** this is much wider than the existing game's 40–90 frame spacing

### Requirement: Level progression

The system SHALL advance through levels, tightening obstacle spacing every 30
obstacles passed.

#### Scenario: Level 2 after 30 obstacles

- **WHEN** the player has passed 30 obstacles without collision
- **THEN** the game level increments to 2
- **AND** the spawn gap range tightens to 120–200 frames
- **AND** a "LEVEL UP" overlay is displayed briefly

#### Scenario: Level progression continues

- **WHEN** the player passes 60, 90, 120+ obstacles
- **THEN** levels advance to 3, 4, 5+
- **AND** each level uses a progressively tighter spawn gap range
- **AND** level 5+ uses the tightest range (60–120 frames)

### Requirement: Speed progression

The system SHALL increase the game speed by a factor of 2.0 per level, applied
multiplicatively. Speed is computed as `BASE_SPEED * SPEED_MULTIPLIER^(level - 1)`
with `SPEED_MULTIPLIER = 2.0`.

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

### Requirement: Collision and game over

The system SHALL detect collisions between the Mario character and obstacles
and end the game on impact.

#### Scenario: Character hits obstacle

- **WHEN** the character's bounding box overlaps an obstacle's bounding box
- **THEN** the system transitions to GAME_OVER state
- **AND** the game stops spawning and moving obstacles
- **AND** the final score (obstacles passed) and level are displayed

#### Scenario: Obstacle passed without collision

- **WHEN** an obstacle's right edge moves past the character's x position
  without collision
- **THEN** the passed-obstacle counter increments by 1

### Requirement: Game states and restart

The system SHALL support three game states: MENU, PLAYING, and GAME_OVER.

#### Scenario: Game over screen displayed

- **WHEN** the character collides with an obstacle
- **THEN** the system displays "GAME OVER — Score: N — Level: L" on the
  Mario-themed background
- **AND** the system waits for SPACE to be pressed

#### Scenario: Restart from game over

- **WHEN** the system is in GAME_OVER state and the user presses SPACE
- **THEN** the system resets all game state (score, level, speed, player
  position, obstacles, jump baseline) and transitions to PLAYING

#### Scenario: Quit the game

- **WHEN** the application window is focused and the user presses `q` or ESC
- **THEN** the system closes all windows, releases the camera, and exits

### Requirement: HUD display

The system SHALL display on-screen information during gameplay.

#### Scenario: Score, level, and speed shown during play

- **WHEN** the game is PLAYING
- **THEN** the system overlays the current score (obstacles passed), current
  level, and the current speed multiplier on the frame in the top-left corner

### Requirement: Mario character torso rendered solid

The system SHALL render the Mario miniatura's torso as a filled solid region in
the red shirt color, so the chest does not look hollow.

#### Scenario: Torso filled with red shirt color

- **WHEN** the Mario character is rendered with a detected pose
- **THEN** the torso quadrilateral (between the shoulders and the hips) is
  filled with a solid red (shirt) color
- **AND** the Mario head and the red/blue body lines continue to render on top
  as before

### Requirement: Character stays inside the visible area during jumps

The system SHALL keep the whole Mario character inside the visible game area at
all times, including during jumps and double jumps.

#### Scenario: Jump does not leave the top of the screen

- **WHEN** the character jumps and reaches its highest point (including a
  double jump)
- **THEN** the entire character remains fully inside the visible area
- **AND** no part of the character (head, arms, or legs) is clipped off the
  top of the screen

