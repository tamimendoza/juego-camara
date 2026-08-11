# mario-sounds-and-double-jump Specification

## Purpose
TBD - created by archiving change mario-sounds-and-double-jump. Update Purpose after archive.
## Requirements
### Requirement: Pose-based jump detection

The system SHALL detect a player jump from body pose landmarks and trigger the
character to jump.

#### Scenario: Double jump detected from second physical jump

- **WHEN** the player performs a second physical jump gesture while the
  character is still airborne
- **THEN** the system triggers a second jump for the on-screen character
- **AND** the character receives an additional upward velocity boost
- **AND** a third jump gesture while airborne does not trigger another jump

