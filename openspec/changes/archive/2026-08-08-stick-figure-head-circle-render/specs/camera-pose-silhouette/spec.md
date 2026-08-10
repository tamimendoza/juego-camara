## ADDED Requirements

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
