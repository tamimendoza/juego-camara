## Purpose

Squares appear in the sky. When the character jumps and touches a sky block, the
player gains 1 life (up to a maximum of 3). A coin sound effect plays. Each sky
block holds only 1 life and disappears after being collected.

## ADDED Requirements

### Requirement: Sky blocks appear in the sky

The system SHALL render square blocks at various positions in the upper portion of
the screen (above the character's ground level).

#### Scenario: Blocks spawn in the sky

- **WHEN** the game is in PLAYING state
- **THEN** square blocks appear at random x positions in the sky region (y <
  ground_y)
- **AND** blocks move leftward at the current game speed

#### Scenario: Blocks respawn over time

- **WHEN** a block moves off the left edge of the screen or is collected
- **THEN** a new block spawns at the right edge after a random interval

### Requirement: Collecting a block grants a life

The system SHALL increment the life count by 1 (up to max 3) when the character
touches a sky block.

#### Scenario: Character touches block while jumping

- **WHEN** the character's bounding box overlaps a sky block's bounding box during
  a jump
- **THEN** the system increments the life count by 1 (capped at 3)
- **AND** the block disappears
- **AND** a coin sound effect plays
- **AND** if the player already has 3 lives, no life is added but the coin sound
  still plays

### Requirement: Blocks hold only 1 life each

Each sky block SHALL contain exactly 1 life. After collection, the block is
removed.

#### Scenario: Block disappears after collection

- **WHEN** a sky block is collected by the character
- **THEN** the block is removed from the game
- **AND** no additional lives can be obtained from that same block
