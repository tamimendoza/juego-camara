# game-brick-ground Delta Spec

## MODIFIED Requirements

### Requirement: Graffiti text on ground

The system SHALL render the text "Familia Mendoza Silva" as graffiti on the
ground.

#### Scenario: Graffiti text appears on the ground

- **WHEN** the game is in PLAYING state
- **THEN** the text "Familia Mendoza Silva" is drawn on the ground area
- **AND** the text is styled to resemble graffiti (white or bright color with
  outline for readability)

#### Scenario: Graffiti text sits on the bricks

- **WHEN** the game is in PLAYING state in the Mario Face Jump variant
- **THEN** the text "Familia Mendoza Silva" is drawn over the brick area,
  below the ground line (`ground_y`)
- **AND** the text does not overlap the sky region above the ground
