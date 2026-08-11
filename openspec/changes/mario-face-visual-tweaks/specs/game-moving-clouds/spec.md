# game-moving-clouds Delta Spec

## ADDED Requirements

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
