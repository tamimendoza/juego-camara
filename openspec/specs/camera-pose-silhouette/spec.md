# camera-pose-silhouette Specification

## Purpose
Detects a person's full-body pose from a Linux/Ubuntu webcam and draws a silhouette character that mimics the user's movements in real time.
## Requirements
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

The system SHALL detect person poses from each video frame and provide landmark positions for head, arms, legs, and torso.

#### Scenario: Person detected and tracked

- **WHEN** a person is visible in the camera frame
- **THEN** the system detects 33 body landmarks covering the head, arms, torso, and legs

#### Scenario: No person in frame

- **WHEN** no person is detected in the current frame
- **THEN** the system does not draw any silhouette or character
- **AND** the previous frame's landmarks are discarded (no ghosting)

#### Scenario: Multiple people detected and tracked

- **WHEN** two or more people are visible in the camera frame
- **THEN** the system SHALL detect the pose landmarks for each person simultaneously
- **AND** each person's landmarks (33 per person) are provided as a separate `PoseResult` in a list
- **AND** each person is rendered as a distinct colored character

#### Scenario: Fewer people than maximum

- **WHEN** fewer people than the configured `num_poses` are detected
- **THEN** the system returns only the detected poses (no empty placeholder results)

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

### Requirement: Head-circle stick figure rendering style

The system SHALL support a rendering style that draws a circle for the head and lines for the body on a solid black background, hiding the live camera feed entirely.

#### Scenario: User cycles to the head-circle style

- **WHEN** the user presses the `s` key repeatedly from Style 4
- **THEN** the system renders Style 5 with a solid black background, a single filled circle at the nose position for the head, and line segments connecting only body landmarks (shoulders, elbows, wrists, hips, knees, ankles)
- **AND** no face connections, joint dots, or segmentation mask are drawn
- **AND** no camera feed is visible

#### Scenario: Head circle scales with user position

- **WHEN** a person is detected with visible shoulder landmarks (indices 11 and 12)
- **THEN** the head circle is centered at the nose landmark (index 0)
- **AND** the circle radius is proportional to the distance between the left and right shoulders
- **AND** if the nose or shoulders are not visible, the circle is omitted

#### Scenario: Body lines connect only body landmarks

- **WHEN** body landmark connections are available from MediaPipe POSE_CONNECTIONS
- **THEN** the system draws line segments only between body landmarks (indices 11–32)
- **AND** connections involving face landmarks (indices 0–10) are excluded

### Requirement: Model file management

The system SHALL download and manage a MediaPipe pose landmarker model file at startup.

#### Scenario: Model file downloaded on first run

- **WHEN** the application starts and `models/pose_landmarker_lite.task` does not exist
- **THEN** the system downloads the model file from the MediaPipe model registry
- **AND** if the download fails, the system prints a clear error and exits gracefully

#### Scenario: Model file reused on subsequent runs

- **WHEN** the application starts and the model file already exists locally
- **THEN** the system uses the cached file without downloading

### Requirement: Distinct character colors per person

The system SHALL render each detected person as a character with a visually distinct color.

#### Scenario: Two people rendered with different colors

- **WHEN** two people are detected simultaneously
- **THEN** the first person's character is rendered in one color and the second person's in a different color
- **AND** the colors are drawn from a fixed palette for consistency

