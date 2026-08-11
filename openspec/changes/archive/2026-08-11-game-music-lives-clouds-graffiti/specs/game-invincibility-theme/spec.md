## Purpose

InvincibilityTheme.mp3 plays when the player has accumulated 5 or more coins
(obstacles passed), layered on top of the background music.

## ADDED Requirements

### Requirement: Invincibility theme triggers at 5+ coins

The system SHALL begin playing InvincibilityTheme.mp3 when the player's score
(obstacles passed) reaches 5 or more.

#### Scenario: Theme starts at 5 coins

- **WHEN** the player's passed_count reaches 5
- **THEN** the system begins playing InvincibilityTheme.mp3 on a continuous loop
- **AND** the background music (GroundTheme.mp3) continues playing underneath

#### Scenario: Theme continues above 5 coins

- **WHEN** the player's passed_count is greater than 5
- **THEN** InvincibilityTheme.mp3 continues to play

#### Scenario: Theme stops when game ends

- **WHEN** the game transitions to GAME_OVER
- **THEN** the system stops InvincibilityTheme.mp3

### Requirement: Volume mixing with background music

The invincibility theme SHALL play at a volume that does not overpower sound
effects, layered on top of the background music.

#### Scenario: Both music tracks play simultaneously

- **WHEN** the player has 5+ coins and is in PLAYING state
- **THEN** both GroundTheme.mp3 (background) and InvincibilityTheme.mp3
  (foreground layer) play simultaneously
- **AND** sound effects remain audible above both music tracks
