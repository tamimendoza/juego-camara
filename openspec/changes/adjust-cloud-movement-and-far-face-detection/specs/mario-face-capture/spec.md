## MODIFIED Requirements

### Requirement: Face detection from webcam

The system SHALL detect the player's face from the webcam feed using MediaPipe
FaceLandmarker (468 face landmarks), including when the player is far from the
camera and the face appears small in the frame. The detector SHALL use relaxed
confidence thresholds so that distant faces are still accepted.

#### Scenario: Face landmarks detected

- **WHEN** the player is in front of the camera with their face visible
- **THEN** the system runs face landmark detection on the RGB camera frame
- **AND** returns 468 normalized face landmarks for the first detected face

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
- **THEN** the system falls back to the existing Mario head circle (peach face +
  cap + hair arc)
- **AND** the character still mimics pose and jump via PoseLandmarker
