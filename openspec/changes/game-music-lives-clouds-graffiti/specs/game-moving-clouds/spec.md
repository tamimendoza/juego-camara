## Purpose

Clouds drift leftward (similar to block/obstacle movement) to simulate forward
motion in the sky, creating a parallax depth effect.

## ADDED Requirements

### Requirement: Clouds move leftward

The system SHALL animate clouds moving from right to left across the sky at a
speed that simulates forward motion.

#### Scenario: Clouds drift across the sky

- **WHEN** the game is in PLAYING state
- **THEN** all clouds move leftward each frame at a constant drift speed
- **AND** when a cloud moves completely off the left edge, it wraps around to the
  right edge

#### Scenario: Cloud movement is slower than obstacles

- **WHEN** clouds are drifting
- **THEN** the cloud drift speed is slower than the obstacle speed, creating a
  parallax depth effect
