## ADDED Requirements

### Requirement: Character stays inside the visible area during jumps

The system SHALL keep the whole Minecraft Mario character inside the visible
game area at all times, including during jumps and double jumps.

#### Scenario: Jump does not leave the top of the screen

- **WHEN** the character jumps and reaches its highest point (including a
  double jump)
- **THEN** the entire character remains fully inside the visible area
- **AND** no part of the character (head, arms, or legs) is clipped off the
  top of the screen

## MODIFIED Requirements

### Requirement: Pose-based jump detection

The system SHALL detect a player jump from pose landmarks and trigger the
Minecraft Mario character to jump, but only when the player first bends their
legs and then performs an actual jump. Raising the shoulders alone must never
trigger a jump.

#### Scenario: Player physically jumps

- **WHEN** the player bends both legs (crouches) and then performs an actual
  jump so the body rises at least 30 pixels above the crouch baseline in the
  camera feed
- **THEN** the system triggers a jump for the Minecraft Mario character
- **AND** the character applies upward velocity and leaves the ground
- **AND** gravity pulls the character back to the ground line

#### Scenario: No jump from shoulders alone

- **WHEN** the player raises their shoulders by 30 pixels or more but never
  bends their legs
- **THEN** the jump detector does not trigger
- **AND** the character remains on the ground

#### Scenario: No false jump when standing

- **WHEN** the player is standing still or moving slightly within pose noise
- **THEN** the jump detector does not trigger
- **AND** the character remains on the ground

#### Scenario: Crouching without jumping does not fire

- **WHEN** the player bends their legs (crouches) but stands back up without
  jumping
- **THEN** no jump is triggered after the crouch expires
- **AND** the character remains on the ground

#### Scenario: Shoulders not visible

- **WHEN** the shoulders or the legs (knees/ankles) are not detected
- **THEN** the jump detector returns no jump event
- **AND** no ghost jumps are triggered
