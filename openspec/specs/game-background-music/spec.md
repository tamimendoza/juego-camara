# game-background-music Specification

## Purpose
Continuous background music during gameplay using GroundTheme.mp3, with volume
mixing that keeps music below sound-effect levels.
## Requirements
### Requirement: Background music plays during gameplay

The system SHALL play GroundTheme.mp3 as a continuous loop during the PLAYING
state.

#### Scenario: Music starts when game begins

- **WHEN** the game transitions from MENU to PLAYING
- **THEN** the system begins playing GroundTheme.mp3 on a continuous loop
- **AND** the music volume is set below the sound-effect volume level

#### Scenario: Music stops on game over

- **WHEN** the game transitions to GAME_OVER
- **THEN** the system stops the background music

### Requirement: Volume mixing keeps music below SFX

The system SHALL ensure background music never overpowers sound effects.

#### Scenario: Music volume is lower than SFX

- **WHEN** the game is playing with background music active
- **THEN** the background music volume is set to a level that does not mask or
  overpower coin sounds, game-over sounds, or life-gain sounds
- **AND** the background music volume is at most 50% of the sound-effect volume

