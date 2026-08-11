## Purpose

The miniatura character in the game engines (base game, Mario, Minecraft, and
the Mario face variant) mirrors the player so that pointing the hands forward
along the character's path renders the character's arms pointing forward —
instead of in reverse.

## ADDED Requirements

### Requirement: Game character pose is mirrored

The system SHALL mirror the detected pose landmarks in each game engine's
`_update_playing` with `mirror_points()` (swap left/right landmark pairs and
X-flip) before rendering the miniatura character.

#### Scenario: Arms point forward like the player

- **WHEN** the player points both hands forward (toward their physical right,
  which is the image-LEFT on a non-flipped camera)
- **THEN** the miniatura character's left and right arms point FORWARD
  (image-right, along the character's path), not in reverse

#### Scenario: Jump detection is unaffected

- **WHEN** the pose is mirrored in the game engine
- **THEN** jump and pose-warning logic still read the shoulder **y** landmark
  positions, so mirrored **x** coordinates do not change jump detection
