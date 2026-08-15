## MODIFIED Requirements

### Requirement: Sky blocks appear in the sky

The system SHALL render square blocks at various positions in the upper portion of
the screen (above the character's ground level). One square appears for every 5
obstacles successfully passed by the character.

#### Scenario: Blocks spawn in the sky

- **WHEN** the game is in PLAYING state
- **THEN** square blocks appear at random x positions in the sky region (y <
  ground_y)
- **AND** blocks move leftward at the current game speed

#### Scenario: One block spawns per 5 obstacles passed

- **WHEN** the character passes the 5th, 10th, 15th, ... obstacle (a multiple of 5)
- **THEN** a new square block spawns in the sky region (y < ground_y)
- **AND** only one block is spawned per 5-obstacle milestone
- **AND** the block moves leftward at the current game speed

#### Scenario: Blocks respawn over time

- **WHEN** a block moves off the left edge of the screen or is collected
- **THEN** a new block spawns at the right edge when the next 5-obstacle milestone
  is reached

### Requirement: Collecting a block restores a life

The system SHALL restore 1 life when the character touches a sky block, up to the
maximum number of lives.

#### Scenario: Character touches block while jumping

- **WHEN** the character's bounding box overlaps a sky block's bounding box during
  a jump
- **THEN** the system increments the player's lives by 1 (if below the maximum)
- **AND** the block disappears
- **AND** a coin sound effect plays
- **AND** no coin is added when a block is collected

### Requirement: Blocks restore a single life each

Each sky block SHALL restore at most 1 life. After collection, the block is removed.

#### Scenario: Block disappears after collection

- **WHEN** a sky block is collected by the character
- **THEN** the block is removed from the game
- **AND** no additional lives can be restored by that same block
