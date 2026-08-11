## Purpose

When the character is in the air (jumping) and the user performs another jump
gesture, the character does an additional jump from its current airborne position.
This is capped at 2 total jumps per airtime to keep the character on screen.

## ADDED Requirements

### Requirement: Mid-air jump while airborne

The system SHALL allow the character to perform an additional jump while airborne,
applying upward velocity from the character's current position.

#### Scenario: Second jump while in the air

- **WHEN** the character is airborne (not on the ground) and the user performs a
  jump gesture
- **THEN** the system applies an additional upward velocity boost to the character
- **AND** the character's jump count increments
- **AND** the character continues its upward or downward trajectory with the new
  velocity

#### Scenario: Jump cap prevents third jump

- **WHEN** the character has already performed 2 jumps while airborne
- **THEN** the system does NOT apply another jump
- **AND** the character continues falling under gravity

#### Scenario: Jump count resets on landing

- **WHEN** the character returns to the ground (jump_offset >= 0)
- **THEN** the jump count resets to 0
- **AND** the character can perform 2 jumps again on the next airborne cycle
