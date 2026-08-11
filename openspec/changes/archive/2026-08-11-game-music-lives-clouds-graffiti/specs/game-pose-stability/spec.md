## Purpose

Detect when the person is not fully visible in the camera frame (too close, too
far, or partially occluded). When detection degrades, pause the game and display
the text "Acerquese o alejese de la camara" at the top of the screen. The character
remains still (preserving its last known pose) until detection quality improves.

## ADDED Requirements

### Requirement: Detection quality assessment

The system SHALL assess pose detection quality based on the number of visible
landmarks and the shoulder width range.

#### Scenario: Quality check on each frame

- **WHEN** new landmarks are received from the pose detector
- **THEN** the system checks if at least 5 body landmarks are visible
- **AND** the system checks if the shoulder width (distance between landmarks 11
  and 12) falls within the acceptable range [30, 250] pixels

#### Scenario: Poor detection detected

- **WHEN** fewer than 5 landmarks are visible OR the shoulder width is outside the
  acceptable range
- **THEN** the system flags detection quality as poor
- **AND** the game pauses (obstacles stop moving, character stops updating)

### Requirement: Warning message displayed

The system SHALL display the text "Acerquese o alejese de la camara" at the top
of the screen when detection quality is poor.

#### Scenario: Warning text appears at top of screen

- **WHEN** detection quality is flagged as poor
- **THEN** the text "Acerquese o alejese de la camara" is rendered at the top of
  the frame (y ≈ 30)
- **AND** the text is visible in a prominent color (red or yellow)

#### Scenario: Warning disappears when quality improves

- **WHEN** detection quality returns to acceptable levels
- **THEN** the warning text disappears
- **AND** the game resumes normal operation

### Requirement: Character remains still during poor detection

The system SHALL preserve the character's last known pose when detection
degrades, rather than letting it deform, jump around, or disappear.

#### Scenario: Character holds last pose

- **WHEN** detection quality degrades
- **THEN** the character retains its last known rendered pose
- **AND** the character does NOT deform, shrink, or move unexpectedly

### Requirement: Jump detection gated on quality

The system SHALL only register jump gestures when detection quality is good.

#### Scenario: No jump during poor detection

- **WHEN** detection quality is poor
- **THEN** the jump detector does not trigger
- **AND** no jumps are registered to prevent false inputs
