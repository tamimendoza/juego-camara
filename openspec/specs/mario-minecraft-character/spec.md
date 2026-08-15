# mario-minecraft-character Specification

## Purpose
A Minecraft/voxel-style variant of the pose-controlled jumping game. The
player's webcam pose is rendered as a **blocky Mario miniatura** — each body
part is a filled rectangle (voxel) rather than a circle or line — using
Mario's color palette (red cap, peach face, red shirt, blue overalls) against a
Minecraft-themed background (sky-blue, pixel clouds, grass-block ground). The
character still mirrors the player's pose and jump; obstacles (pipes, blocks,
goombas) are rendered as voxel rectangles and spawn with the same level/speed
progression as the existing Mario Bros variant.
## Requirements
### Requirement: Game startup and camera capture

The Minecraft Mario game SHALL open the webcam and display a themed menu screen
waiting for input.

#### Scenario: Menu screen displayed

- **WHEN** the game starts and the camera is opened
- **THEN** the system renders a sky-blue background with pixel-style clouds
  and a grass-block ground band, overlaid with "MINECRAFT MARIO — Press SPACE
  to start"
- **AND** no obstacles are spawned until the game starts

#### Scenario: Game starts on SPACE

- **WHEN** the application is in MENU state and the user presses SPACE
- **THEN** the system transitions to PLAYING state
- **AND** the blocky Mario character appears at ground level
- **AND** obstacles begin spawning from the right edge with wide gaps (level 1)

### Requirement: Pose-based jump detection

The system SHALL detect a player jump from pose landmarks and trigger the
Minecraft Mario character to jump, but only when the player first bends their
legs and then performs an actual jump. Raising the shoulders alone must never
trigger a jump.

#### Scenario: Player physically jumps

- **WHEN** the player bends both legs (crouches) and then performs an actual
  jump so the body rises at least 30 pixels above the crouch baseline in the
  camera feed
- **THEN** the system triggers a jump for the Minecraft Mario character
- **AND** the character applies upward velocity and leaves the ground
- **AND** gravity pulls the character back to the ground line

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

### Requirement: Minecraft-style character rendering

The system SHALL render the player's pose as a blocky Minecraft-styled Mario
character at a fixed horizontal position, using a solid sky-blue background with
no camera feed.

#### Scenario: Character rendered with voxel blocks

- **WHEN** the player is detected
- **THEN** the system renders a square head block centered at the nose landmark
  (index 0), sized by shoulder width
- **AND** the top ~40% of the head is a red cap block
- **AND** the bottom ~60% is a peach face block with two small black pixel eyes
- **AND** the system draws body parts as five **predefined solid rectangle
  segments** (not derived from connection pairs):
  - Torso: red rectangle from shoulder midpoint to hip midpoint
  - Left arm: red rectangle from left shoulder (11) to left wrist (15)
  - Right arm: red rectangle from right shoulder (12) to right wrist (16)
  - Left leg: blue rectangle from left hip (23) to left ankle (27)
  - Right leg: blue rectangle from right hip (24) to right ankle (28)
- **AND** each rectangle has a 1–2px darker border to simulate voxel edges
- **AND** face landmarks (0–10) are not used in body rendering
- **AND** the character is rendered at a fixed x position (80 px from left)
  near the bottom of the screen
- **AND** the character uses a **fixed pixel size** — it does NOT scale based on
  the user's distance from the camera (no "ampliarse" / enlargement)

#### Scenario: Character does not enlarge based on pose distance

- **WHEN** the player moves closer to or farther from the camera
- **THEN** the Minecraft Mario character remains the same fixed pixel size
- **AND** the character's size does not change between frames
- **AND** the character still mirrors the player's pose (arm/leg angles, jump)

#### Scenario: Character remains still when pose detection degrades

- **WHEN** a valid pose was previously detected and then landmarks are lost
  (fewer than 5 visible points due to occlusion or the user leaving the frame)
- **THEN** the character keeps its last known pose — it does not jump around,
  shrink, or morph
- **AND** if the pose is restored, the character smoothly updates to the new pose

#### Scenario: No pose detected — character stays static

- **WHEN** no person is detected in the camera feed
- **THEN** the character does not appear (or shows a static rest pose at ground
  level)
- **AND** the character does not jump, scale, or move

#### Scenario: Character jumps on screen

- **WHEN** a jump is triggered
- **THEN** the entire blocky Mario miniatura moves upward with physics
  (velocity + gravity)
- **AND** returns to the ground line when landing

#### Scenario: No pose detected — fallback rendering

- **WHEN** landmarks are not available for a frame
- **THEN** the system renders a static fallback blocky Mario figure at the
  character's last ground position (head block + cap + single body rectangle)

### Requirement: Minecraft-themed background

The system SHALL render a Minecraft-style background behind the character and
obstacles.

#### Scenario: Sky, clouds, and grass-block ground drawn

- **WHEN** the game is in PLAYING state
- **THEN** the system fills the frame with sky blue (BGR 235, 206, 135)
- **AND** draws 3–4 pixel-style white clouds (stitched rectangles) at fixed
  positions in the upper half
- **AND** draws a grass-block ground band at the bottom 15% of the screen:
  - Top 20% of the band: green (grass surface, BGR 0, 160, 60)
  - Bottom 80% of the band: brown (dirt, BGR 80, 60, 30)
  - Dark brown border lines to simulate block texture

### Requirement: Obstacle spawning and movement

The system SHALL spawn Mario-themed obstacles (pipes, blocks, goombas) as
voxel-style rectangles from the right edge that move leftward at the current
game speed.

#### Scenario: Obstacle appears at right edge

- **WHEN** the game is PLAYING
- **THEN** obstacles spawn at the right edge of the screen (x = width)
- **AND** each obstacle is rendered as a filled rectangle with a dark border
  (pipe: green 40×80, block: orange 40×40 with "?" text, goomba: red-brown 30×30
  with white pixel eyes)
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

The system SHALL increase the game speed every 10 obstacles successfully passed.

#### Scenario: Speed increases after 10 obstacles

- **WHEN** the player has passed 10 obstacles without collision
- **THEN** the game speed is multiplied by 1.10
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

### Requirement: Collision and game over

The system SHALL detect collisions between the Minecraft Mario character and
obstacles and end the game on impact.

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
  Minecraft-themed background
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
- **AND** the HUD text uses a simple monospace style (white with black outline)
  for readability against the sky background

### Requirement: Character stays inside the visible area during jumps

The system SHALL keep the whole Minecraft Mario character inside the visible
game area at all times, including during jumps and double jumps.

#### Scenario: Jump does not leave the top of the screen

- **WHEN** the character jumps and reaches its highest point (including a
  double jump)
- **THEN** the entire character remains fully inside the visible area
- **AND** no part of the character (head, arms, or legs) is clipped off the
  top of the screen

