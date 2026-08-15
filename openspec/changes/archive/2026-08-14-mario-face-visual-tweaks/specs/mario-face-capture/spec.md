# mario-face-capture Delta Spec

## ADDED Requirements

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
