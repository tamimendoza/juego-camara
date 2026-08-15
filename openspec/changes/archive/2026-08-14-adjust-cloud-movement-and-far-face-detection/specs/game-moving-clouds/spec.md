## MODIFIED Requirements

### Requirement: Clouds move leftward

The system SHALL animate all clouds moving from right to left across the sky at a
speed that simulates forward motion. During gameplay every cloud visible in the sky
SHALL be part of the moving cloud layer; the sky SHALL be populated with moving
clouds as soon as a game (or a round after game over) starts.

#### Scenario: Clouds drift across the sky

- **WHEN** the game is in PLAYING state
- **THEN** all clouds visible in the sky move leftward each frame at a constant
  drift speed
- **AND** when a cloud moves completely off the left edge, it is removed and a new
  cloud is spawned at the right edge

#### Scenario: No static clouds during gameplay

- **WHEN** the game is in PLAYING state
- **THEN** no cloud is drawn at a fixed, non-moving position in the sky
- **AND** every rendered cloud belongs to the moving cloud layer

#### Scenario: Sky populated at game start

- **WHEN** a game starts or restarts after game over
- **THEN** the moving cloud layer already contains clouds distributed across the sky
- **AND** clouds continue to spawn from the right edge over time

#### Scenario: Cloud movement is slower than obstacles

- **WHEN** clouds are drifting
- **THEN** the cloud drift speed is slower than the obstacle speed, creating a
  parallax depth effect
