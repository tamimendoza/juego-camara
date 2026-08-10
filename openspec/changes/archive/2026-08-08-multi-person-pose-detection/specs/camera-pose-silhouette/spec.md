## MODIFIED Requirements

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

## ADDED Requirements

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
