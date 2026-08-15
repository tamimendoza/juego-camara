# system-notification-suppression Specification

## Purpose
Suppresses desktop notification banners for the entire duration of a game
session so notifications do not interrupt play, and restores them when the
game exits.

## Requirements

### Requirement: Suppress notifications while the game runs

The system SHALL suppress desktop notification banners from the moment the
game starts until the game exits, on any desktop that supports suppression.

#### Scenario: Game launches on a supported desktop

- **WHEN** the game starts on a desktop with a supported suppression mechanism
- **THEN** the system activates notification suppression before the game loop
  begins
- **AND** the suppression remains active for the whole session, regardless of
  the game state (menu, name entry, playing, game over)

#### Scenario: Game exits

- **WHEN** the game exits (normal quit, error, or signal)
- **THEN** the system deactivates notification suppression and restores the
  desktop's original notification setting

### Requirement: Graceful degradation on unsupported environments

The system SHALL not fail to start the game when no supported suppression
mechanism is available.

#### Scenario: No desktop session or unsupported desktop

- **WHEN** the game starts on a headless machine, in CI, or on a desktop
  without a supported suppression mechanism
- **THEN** the game still starts and runs normally
- **AND** no suppression is attempted

#### Scenario: Suppression mechanism fails at runtime

- **WHEN** activating or deactivating suppression fails (missing command,
  D-Bus error, or permission denied)
- **THEN** the game continues running normally
- **AND** the failure is reported silently without raising an exception

### Requirement: Restore original notification state

The system SHALL restore the desktop's notification settings to their original
state when the game exits, even if only part of the session was suppressed.

#### Scenario: Original setting restored after play

- **WHEN** the game session ends after suppression was activated
- **THEN** the desktop's notification setting is exactly as it was before the
  game started

#### Scenario: Suppression activation partially succeeded

- **WHEN** some suppression steps succeed and others fail during a session
- **THEN** the system still restores every setting it changed