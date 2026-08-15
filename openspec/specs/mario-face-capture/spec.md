# mario-face-capture Specification

## Purpose

A Mario Bros-themed pose-controlled jumping game variant where the player's
real face (captured from the webcam via MediaPipe FaceMesh) replaces the
Mario head entirely. The character still mimics the player's pose and jump via
PoseLandmarker body landmarks, but the head is a real face crop instead of a
peach face circle + cap + hair arc. The Mario body lines (red shirt for
arms/torus, blue overalls for legs) are preserved.
## Requirements
### Requirement: Face detection from webcam

The system SHALL detect the player's face from the webcam feed using the
MediaPipe Tasks API FaceLandmarker (`models/face_landmarker.task`, 468 face
landmarks), replacing the legacy FaceMesh solution API. Detection SHALL work
even when the player is far from the camera and the face appears small in the
frame; the detector SHALL use relaxed confidence thresholds so that distant
faces are still accepted.

#### Scenario: Face landmarks detected

- **WHEN** the player is in front of the camera with their face visible
- **THEN** the system runs the FaceLandmarker Tasks API on the RGB camera
  frame
- **AND** returns 468 normalized face landmarks for the first detected face
- **AND** returns a face bounding box when the model supports it

#### Scenario: Face detected from a distance

- **WHEN** the player is far from the camera so the face appears small in the frame
- **THEN** the system still detects the face and returns its landmarks
- **AND** the face crop is still overlaid on the character's head

#### Scenario: Relaxed confidence thresholds used

- **WHEN** the face detector is configured
- **THEN** `min_face_detection_confidence` and `min_tracking_confidence` are set
  below `0.5`
- **AND** `min_face_presence_confidence` is set low enough not to reject distant
  faces

#### Scenario: No face detected

- **WHEN** the player's face is not visible or detection fails even with the
  relaxed thresholds
- **THEN** the system falls back to the existing Mario head circle (peach
  face + cap + hair arc)
- **AND** the character still mimics pose and jump via PoseLandmarker

### Requirement: Face cropping from camera frame

The system SHALL crop a circular face region from the BGR camera frame using
the FaceLandmarker face bounding box (when available) for a tighter, more
efficient crop, falling back to face contour landmarks when the bounding box
is not provided.

#### Scenario: Face region cropped

- **WHEN** FaceLandmarker returns face landmarks (and optionally a face bounding box)
- **THEN** the system uses the face bounding box to determine the face crop
  region and center
- **AND** crops a circular region centered on the face
- **AND** creates a circular mask
- **AND** returns the cropped face image (BGR) at the target radius
- **AND** when no bounding box is available, the system falls back to using face
  contour landmarks (indices 1–200), centering at the nose tip (landmark 1), as
  in the previous implementation

#### Scenario: Face crop size matches head circle

- **WHEN** the face is cropped
- **THEN** the crop radius equals `max(int(shoulder_width * 0.25), 10)` pixels
  (same as the current Mario head circle radius)

### Requirement: Face overlay replaces Mario head

The system SHALL overlay the cropped real face at the character's head
position, replacing the peach face circle, red cap, and brown hair arc
entirely.

#### Scenario: Real face shown instead of Mario head

- **WHEN** the character is rendered with pose detected
- **THEN** the system overlays the cropped face image at the nose landmark
  position (PoseLandmarker index 0)
- **AND** no peach face circle is drawn
- **AND** no red cap is drawn
- **AND** no brown hair arc is drawn
- **AND** the face is rendered as a circular crop with a circular mask

#### Scenario: Mario body lines preserved

- **WHEN** the character is rendered
- **THEN** the system draws body lines in Mario colours: red for arms/torso
  (shirt) and blue for legs (overalls)
- **AND** face connections (FaceMesh landmarks) are not drawn as skeleton lines
- **AND** the character is rendered at a fixed x position (80 px from left)
  near the bottom of the screen

#### Scenario: Character jumps with face overlay

- **WHEN** a jump is triggered
- **THEN** the entire character (including the face overlay) moves upward
  with physics (velocity + gravity)
- **AND** returns to the ground line when landing

### Requirement: Game startup and camera capture

The system SHALL open the webcam and display a themed name-entry screen waiting
for input, with the FaceLandmarker detector initialized alongside PoseLandmarker.

#### Scenario: Menu screen displayed

- **WHEN** the game starts and the camera is opened
- **THEN** the system renders a sky-blue background with drawn clouds, bushes,
  and a brick ground, overlaid with a name-entry prompt for the player
- **AND** the player's typed name is shown as it is entered
- **AND** no obstacles are spawned until the game starts

#### Scenario: Game starts on SPACE

- **WHEN** the application is in name-entry state and the user presses ENTER
  after typing a non-empty name
- **THEN** the system transitions to PLAYING state
- **AND** the Mario face character appears at ground level
- **AND** obstacles begin spawning from the right edge with wide gaps (level 1)

### Requirement: Pose-based jump detection

The system SHALL detect a player jump from body pose landmarks and trigger the
Mario character to jump, using the same jump detector as the existing Mario
game, but only when the player first bends their legs and then performs an
actual jump. Raising the shoulders alone must never trigger a jump.

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

### Requirement: Mario-themed background

The system SHALL render a Mario Bros-style background behind the character
and obstacles, identical to the existing Mario game.

#### Scenario: Sky, clouds, bushes, and ground drawn

- **WHEN** the game is in PLAYING state
- **THEN** the system fills the frame with sky blue
- **AND** draws white fluffy clouds at fixed positions
- **AND** draws green bushes with red flowers near the ground
- **AND** draws a brown brick-patterned ground band at the bottom 15% of the
  screen

### Requirement: Obstacle spawning and movement

The system SHALL spawn Mario-themed obstacles (pipes, blocks, goombas) from
the right edge of the screen that move leftward at the current game speed,
identical to the existing Mario game.

#### Scenario: Obstacle appears at right edge

- **WHEN** the game is PLAYING
- **THEN** obstacles spawn at the right edge of the screen (x = width)
- **AND** each obstacle is one of three types: pipe (green, 40x80), block
  (orange, 40x40), or goomba (red-brown, 30x30)
- **AND** obstacle types cycle sequentially (pipe -> block -> goomba -> pipe ...)

#### Scenario: Obstacles move leftward

- **WHEN** an obstacle is spawned
- **THEN** it moves leftward each frame at the current game speed
- **AND** when it moves completely off the left edge (x + width < 0), it is
  removed from the game

#### Scenario: Wide obstacle spacing at level 1

- **WHEN** the player is at level 1 (0 obstacles passed)
- **THEN** obstacles spawn at intervals of 180-280 frames
- **AND** this is much wider than the existing game's 40-90 frame spacing

### Requirement: Level progression

The system SHALL advance through levels, tightening obstacle spacing every 5
obstacles passed, identical to the existing Mario game.

#### Scenario: Level 2 after 5 obstacles

- **WHEN** the player has passed 5 obstacles without collision
- **THEN** the game level increments to 2
- **AND** the spawn gap range tightens to 150-250 frames
- **AND** a "LEVEL UP" overlay is displayed briefly

#### Scenario: Level progression continues

- **WHEN** the player passes 10, 15, 20+ obstacles
- **THEN** levels advance to 3, 4, 5+
- **AND** each level uses a progressively tighter spawn gap range
- **AND** level 6+ uses the tightest range (70-130 frames)

### Requirement: Speed progression

The system SHALL increase the game speed every 10 obstacles successfully
passed, identical to the existing Mario game.

#### Scenario: Speed increases after 10 obstacles

- **WHEN** the player has passed 10 obstacles without collision
- **THEN** the game speed is multiplied by 1.10
- **AND** existing obstacles adopt the new speed immediately
- **AND** new obstacles spawn at the new speed

### Requirement: Collision and game over

The system SHALL detect collisions between the Mario character and obstacles
and end the game on impact, identical to the existing Mario game.

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

The system SHALL support the game states name entry, PLAYING, and GAME_OVER,
and return to the name-entry screen when restarting.

#### Scenario: Game over screen displayed

- **WHEN** the character collides with an obstacle and loses all lives
- **THEN** the system displays "GAME OVER" with the final score, level, speed,
  and coins on the Mario-themed background
- **AND** the system displays the Top 5 leaderboard ordered by coins
- **AND** the system waits for ENTER to be pressed

#### Scenario: Restart from game over

- **WHEN** the system is in GAME_OVER state and the user presses ENTER
- **THEN** the system shows the name-entry screen with an empty name field
- **AND** does not resume the previous game until a new name is confirmed

#### Scenario: Quit the game

- **WHEN** the application window is focused and the user presses `q` or ESC
- **THEN** the system closes all windows, releases the camera, and exits

### Requirement: HUD display

The system SHALL display on-screen information during gameplay, including the
name of the current player, identical to the existing Mario game.

#### Scenario: Score, level, and speed shown during play

- **WHEN** the game is PLAYING
- **THEN** the system overlays the current score (obstacles passed), current
  level, the current speed multiplier, and the name of the current player on
  the frame in the top-left corner

### Requirement: Live face preview circle

The system SHALL display a small circular live preview of the detected face in
the lower-right area of the screen, over the bricks, so the player can verify
that the face fits and is centered in the head circle when standing far from
the camera.

#### Scenario: Face detected while playing

- **WHEN** the game is in PLAYING state and a face is detected
- **THEN** the system draws the cropped face in a small circle at the lower-right
  corner of the screen (on the brick area)
- **AND** the preview shows the same face crop used for the character's head
- **AND** the preview is small and positioned so it does not interrupt gameplay

#### Scenario: No face detected while playing

- **WHEN** the game is in PLAYING state and no face is detected
- **THEN** the system shows an empty/outline circle at the lower-right corner
  (or hides the preview content)
- **AND** the game continues normally

#### Scenario: Face preview visible in all playing states

- **WHEN** the player is playing, paused by the pose warning, or on the game
  over overlay
- **THEN** the face preview circle remains visible so the player can adjust
  their distance to the camera

### Requirement: Mario Face character torso rendered solid

The system SHALL render the Mario Face miniatura's torso as a filled solid
region in the red shirt color, so the chest does not look hollow.

#### Scenario: Torso filled with red shirt color

- **WHEN** the Mario Face character is rendered with a detected pose
- **THEN** the torso quadrilateral (between the shoulders and the hips) is
  filled with a solid red (shirt) color
- **AND** the face overlay and the red/blue body lines continue to render on
  top as before

### Requirement: Character stays inside the visible area during jumps

The system SHALL keep the whole Mario Face character inside the visible game
area at all times, including during jumps and double jumps.

#### Scenario: Jump does not leave the top of the screen

- **WHEN** the character jumps and reaches its highest point (including a
  double jump)
- **THEN** the entire character remains fully inside the visible area
- **AND** no part of the character (face, arms, or legs) is clipped off the
  top of the screen

