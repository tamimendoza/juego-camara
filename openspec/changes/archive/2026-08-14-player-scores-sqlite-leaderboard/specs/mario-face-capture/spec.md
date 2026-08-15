## MODIFIED Requirements

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