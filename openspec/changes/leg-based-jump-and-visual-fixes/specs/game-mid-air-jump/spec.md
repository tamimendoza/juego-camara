## MODIFIED Requirements

### Requirement: Mid-air jump while airborne

The system SHALL allow the character to perform an additional jump while
airborne, applying upward velocity from the character's current position, but
only when the player performs the two-phase leg gesture in the air (bends/tucks
the legs and then extends them / rises). The resulting apex is capped so the
character never leaves the visible area.

#### Scenario: Second jump while in the air

- **WHEN** the character is airborne (not on the ground) and the player bends
  their legs (tucks) and then performs an actual jump (legs extend / body
  rises)
- **THEN** the system applies an additional upward velocity boost to the
  character
- **AND** the character's jump count increments
- **AND** the character continues its upward or downward trajectory with the
  new velocity

#### Scenario: No double jump from a bare shoulder rise

- **WHEN** the character is airborne and the player raises their shoulders
  without bending their legs
- **THEN** the system does NOT apply another jump
- **AND** the character continues falling under gravity

#### Scenario: Double jump apex capped on screen

- **WHEN** the double jump is performed
- **THEN** the character's apex is capped so the whole character stays inside
  the visible area
- **AND** no part of the character is clipped off the top of the screen

#### Scenario: Jump cap prevents third jump

- **WHEN** the character has already performed 2 jumps while airborne
- **THEN** the system does NOT apply another jump
- **AND** the character continues falling under gravity

#### Scenario: Jump count resets on landing

- **WHEN** the character returns to the ground (jump_offset >= 0)
- **THEN** the jump count resets to 0
- **AND** the character can perform 2 jumps again on the next airborne cycle
