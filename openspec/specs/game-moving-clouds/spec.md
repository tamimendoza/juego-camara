# game-moving-clouds Specification

## Purpose
Clouds drift leftward (similar to block/obstacle movement) to simulate forward
motion in the sky, creating a parallax depth effect.
## Requirements
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

### Requirement: Clouds render as cloud sprites

The system SHALL render every moving cloud during gameplay using a cloud-shaped
sprite (extracted from the sprite sheet) instead of a single plain ellipse.

#### Scenario: Cloud drawn with cloud sprite

- **WHEN** a moving cloud is rendered during gameplay
- **THEN** the cloud is drawn using the cloud sprite image
- **AND** the sprite is scaled to the cloud's width and height
- **AND** the sprite's transparency is preserved so the sky shows through

#### Scenario: Cloud sprite applies to all moving clouds

- **WHEN** any cloud in the moving cloud layer is rendered
- **THEN** the cloud sprite rendering is used for every moving cloud
- **AND** no moving cloud is drawn as a plain single ellipse

### Requirement: Clouds keep a wide cloud-like proportion

The system SHALL render moving clouds with a wide, flat proportion so that
they are perceived as clouds and not as fire or flames.

#### Scenario: Cloud height is cropped

- **WHEN** a cloud with a sprite is spawned in the Mario Face Jump variant
- **THEN** the cloud is drawn with a height smaller than its width, preserving
  the wide aspect ratio of the cloud sprite
- **AND** the cloud does not appear stretched vertically like a flame

#### Scenario: Cloud proportions do not break parallax movement

- **WHEN** a cloud is resized with the cropped height
- **THEN** the cloud still moves leftward at the drift speed and wraps/removes
  off the left edge as before

