## Purpose

The game display windows (base game, Mario Bros, Minecraft Mario, and Mario
Face) open at a fixed size and cannot be resized, stretched, or zoomed by the
user, so the rendered game screen is never scaled or distorted.

## ADDED Requirements

### Requirement: Game window is fixed-size

The system SHALL open each game window at its native resolution without
allowing the user to resize or zoom the displayed game screen.

#### Scenario: Window opens at native size

- **WHEN** any of the four game modes starts
- **THEN** the window opens at the game's fixed resolution (640×480)
- **AND** the displayed game content cannot be scaled up or down by the user

#### Scenario: No resize or zoom interaction

- **WHEN** the user attempts to resize the window or zoom into the game screen
- **THEN** the window size does not change
- **AND** the game screen is not zoomed, stretched, or distorted
