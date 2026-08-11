## MODIFIED Requirements

### Requirement: Character mimics user movements

The system SHALL render a character whose pose mirrors the detected user's pose in real time.

#### Scenario: Character follows arm movements

- **WHEN** the user raises, lowers, or moves their arms
- **THEN** the character's arm polygons update position to match the detected elbow and wrist
  landmark positions within one frame
- **AND** the movement is smooth (no jitter from raw landmark noise)

#### Scenario: Character follows leg and head movements

- **WHEN** the user moves their legs or head
- **THEN** the character's leg and head polygons follow the detected landmark
  positions in real time

#### Scenario: Mirror mode

- **WHEN** the user presses the `m` key
- **THEN** the system toggles mirror mode, reflecting the character horizontally
  by X-flipping all landmark coordinates AND swapping each pair of symmetric
  left/right body landmark indices (shoulder, elbow, wrist, hip, knee, ankle,
  heel, and foot-index pairs)
- **AND** an arm pointing backward relative to the body centerline in real life
  remains pointing backward in the mirrored character (direction preserved)
- **AND** head/face landmarks (indices 0–10, which are mostly midline or
  asymmetric) are X-flipped only without index swapping

#### Scenario: Real-time frame rate

- **WHEN** the application is running with a person in frame
- **THEN** the system SHALL render at 30 or more frames per second on standard Ubuntu hardware
