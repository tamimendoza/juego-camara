## MODIFIED Requirements

### Requirement: Face detection from webcam

The system SHALL detect the player's face from the webcam feed using the
MediaPipe Tasks API FaceLandmarker (`models/face_landmarker.task`, 468 face
landmarks), replacing the legacy FaceMesh solution API.

#### Scenario: Face landmarks detected

- **WHEN** the player is in front of the camera with their face visible
- **THEN** the system runs the FaceLandmarker Tasks API on the RGB camera
  frame
- **AND** returns 468 normalized face landmarks for the first detected face
- **AND** returns a face bounding box when the model supports it

#### Scenario: No face detected

- **WHEN** the player's face is not visible or FaceLandmarker fails to detect
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

### Requirement: Game startup and camera capture

The system SHALL open the webcam and display a themed menu screen waiting
for input, with the FaceLandmarker detector initialized alongside
PoseLandmarker.

#### Scenario: Menu screen displayed

- **WHEN** the game starts and the camera is opened
- **THEN** the system renders a sky-blue background with drawn clouds, bushes,
  and a brick ground, overlaid with "MARIO FACE JUMP — Press SPACE to start"
- **AND** no obstacles are spawned until the game starts

#### Scenario: Game starts on SPACE

- **WHEN** the application is in MENU state and the user presses SPACE
- **THEN** the system transitions to PLAYING state
- **AND** the Mario face character appears at ground level
- **AND** obstacles begin spawning from the right edge with wide gaps (level 1)
