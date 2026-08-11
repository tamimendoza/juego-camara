## ADDED Requirements

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
