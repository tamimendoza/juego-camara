# game-brick-ground Specification

## Purpose
The ground is rendered with a brick color and brick pattern, and the text "Familia
Mendoza Silva" is drawn as graffiti on the ground.
## Requirements
### Requirement: Brick-colored ground

The system SHALL render the ground area (below the character's standing line)
with a brick color and a brick-pattern texture.

#### Scenario: Ground has brick color and pattern

- **WHEN** the game is in PLAYING state
- **THEN** the ground is filled with a brick-red/brown color
- **AND** a brick pattern (individual brick rectangles with mortar lines) is
  drawn across the ground area

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

