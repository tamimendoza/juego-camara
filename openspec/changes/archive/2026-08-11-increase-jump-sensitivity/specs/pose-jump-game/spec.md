## MODIFIED Requirements

### Requirement: Pose-based jump detection

The system SHALL detect a player jump from body pose landmarks and trigger the
character to jump.

#### Scenario: Player physically jumps

- **WHEN** the player raises their shoulders above the baseline by at least 30
  pixels in the camera feed
- **THEN** the system triggers a jump for the on-screen character
- **AND** the character applies upward velocity and leaves the ground
- **AND** gravity pulls the character back to ground level

#### Scenario: No false jump when standing

- **WHEN** the player is standing still or moving slightly within pose noise
- **THEN** the jump detector does not trigger
- **AND** the character remains on the ground

#### Scenario: Shoulders not visible

- **WHEN** landmarks 11 or 12 (shoulders) are not detected (occluded or out
  of frame)
- **THEN** the jump detector returns no jump event
- **AND** no ghost jumps are triggered

#### Scenario: Rapid re-jump after landing

- **WHEN** the player lands and raises their shoulders above the baseline by
  at least 30 pixels again within a short period
- **THEN** the system SHALL trigger a second jump without requiring the full
  previous cooldown to elapse
- **AND** the cooldown between allowed jump triggers is no more than 8 frames

## ADDED Requirements

### Requirement: Jump clears all obstacle heights

The system SHALL give the miniatura character enough vertical clearance during
a jump to pass over every possible obstacle height without colliding.

#### Scenario: Character clears the tallest obstacle

- **WHEN** the player executes a successful jump (shoulders rise above baseline)
- **THEN** the character's jump apex is at least 20 pixels higher than the
  maximum obstacle height (120 px)
- **AND** the character lands back on the ground without colliding with the
  obstacle

#### Scenario: Jump sensitivity enables timely obstacle clearance

- **WHEN** an obstacle approaches the character and the player initiates a
  jump with a small shoulder movement (at least 30 px)
- **THEN** the jump is triggered with sufficient sensitivity that the character
  clears the obstacle before the character's bounding box overlaps the
  obstacle's bounding box
