## Purpose

Detects a person's full-body pose from a Linux/Ubuntu webcam and draws a silhouette character that mimics the user's movements in real time.

## ADDED Requirements

### Requirement: Camera capture on Linux Ubuntu

The system SHALL capture video from a webcam on Linux Ubuntu using the V4L2 backend.

#### Scenario: Webcam opens successfully

- **WHEN** the application starts on a Linux Ubuntu machine with a webcam at `/dev/video0`
- **THEN** the system opens the camera with `cv2.CAP_V4L2` and captures frames at a configurable resolution
- **AND** the video feed displays in a window titled "Juego Camara"

#### Scenario: Camera not available

- **WHEN** no webcam is detected or the camera is already in use
- **THEN** the system prints a clear error message and exits gracefully without crashing

### Requirement: Real-time full-body pose detection

The system SHALL detect a person's pose from each video frame and provide landmark positions for head, arms, legs, and torso.

#### Scenario: Person detected and tracked

- **WHEN** a person is visible in the camera frame
- **THEN** the system detects 33 body landmarks covering the head, arms, torso, and legs
- **AND** landmarks are updated on every frame at real-time speed (30+ FPS target)

#### Scenario: No person in frame

- **WHEN** no person is detected in the current frame
- **THEN** the system does not draw any silhouette or character
- **AND** the previous frame's landmarks are discarded (no ghosting)

### Requirement: Silhouette drawing on camera feed

The system SHALL draw a colored silhouette overlay on the live camera feed that matches the detected person's body shape.

#### Scenario: Segmentation mask silhouette appears

- **WHEN** a person is detected with segmentation enabled
- **THEN** the system extracts the person's segmentation mask from MediaPipe
- **AND** draws a filled silhouette using the mask contour overlaid on the camera frame
- **AND** the silhouette's color is configurable

#### Scenario: Landmark-based skeleton character

- **WHEN** pose landmarks are detected for a visible person
- **THEN** the system draws body-part polygons connecting the joints:
  - Head polygon from face landmarks (nose, eyes, ears, mouth)
  - Torso quadrilateral from shoulders and hips
  - Upper arm triangles from shoulder to elbow to wrist
  - Leg triangles from hip to knee to ankle
- **AND** each body part is filled with a distinct color

#### Scenario: Visibility-filtered landmark drawing

- **WHEN** a body part landmark has a visibility below the threshold
- **THEN** the system does not draw that landmark or any connection to it
- **AND** no phantom lines are drawn to occluded or out-of-frame body parts

### Requirement: Character mimics user movements

The system SHALL render a character whose pose mirrors the detected user's pose in real time.

#### Scenario: Character follows arm movements

- **WHEN** the user raises, lowers, or moves their arms
- **THEN** the character's arm polygons update position to match the detected elbow and wrist landmarks within one frame
- **AND** the movement is smooth (no jitter from raw landmark noise)

#### Scenario: Character follows leg and head movements

- **WHEN** the user moves their legs or head
- **THEN** the character's leg and head polygons follow the detected landmark positions in real time

#### Scenario: Mirror mode

- **WHEN** the user presses the `m` key
- **THEN** the system toggles mirror mode (character moves symmetrically with the user as if reflected)

#### Scenario: Real-time frame rate

- **WHEN** the application is running with a person in frame
- **THEN** the system SHALL render at 30 or more frames per second on standard Ubuntu hardware

### Requirement: Landmark smoothing

The system SHALL smooth landmark positions across frames to reduce jitter in the character's movement.

#### Scenario: Smooth character rendering

- **WHEN** the user is standing still
- **THEN** the character's silhouette polygon vertex positions do not jitter more than ±2 pixels between consecutive frames

### Requirement: Application controls

The system SHALL respond to keyboard input for controlling the application.

#### Scenario: User quits application

- **WHEN** the user presses the `q` key while the application window is focused
- **THEN** the system closes all windows and releases the camera

#### Scenario: User toggles silhouette style

- **WHEN** the user presses the `s` key while the application window is focused
- **THEN** the system cycles through available silhouette rendering styles (e.g., filled, outline, overlay)
