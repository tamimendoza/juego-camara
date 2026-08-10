## Why

The game needs a richer audiovisual experience: background music, a lives system with
visible hearts, moving clouds for depth, sky blocks that reward extra lives, and a
brick-ground with family graffiti. Additionally, the level progression interval should
change from every 10 obstacles to every 5, and the game should pause with a camera-
distance warning when pose detection degrades. These features apply consistently across
all three game variants (base, Mario, Minecraft) per the project's cross-variant
consistency requirement.

## What Changes

- **Background music**: `@sounds/GroundTheme.mp3` plays continuously during gameplay at
  a volume that never exceeds sound effects.
- **Invincibility theme**: `@sounds/InvincibilityTheme.mp3` plays when the player has
  5 or more coins (obstacles passed), layered on top of the background music.
- **Level progression**: Change `LEVEL_INTERVAL` from 10 to 5 across all three game
  variants. Every 5 obstacles passed, the level increments and speed increases.
- **Obstacle passing safety**: Ensure obstacles that have already been passed (coin
  sound already played) do not trigger collision detection — the `passed` flag must
  prevent re-collision.
- **Pose stability**: When the person is not fully detected (too few visible
  landmarks or out-of-range shoulder width), pause the game and display the text
  "Acerquese o alejese de la camara" at the top of the screen.
- **Lives system**: The character has 3 lives, rendered as 3 hearts in the HUD.
  Each obstacle collision that is not cleared (player fails to jump) costs one life.
  Hearts disappear as lives are lost. Game over when all lives are gone.
- **Moving clouds**: Clouds drift leftward (similar to obstacle/block movement) to
  simulate forward motion in the sky.
- **Sky blocks**: Squares appear in the sky. When the character jumps and touches a
  sky block, the player gains 1 life (max 3). A coin sound effect plays. Each block
  holds only 1 life.
- **Brick ground**: The ground is rendered with a brick color and pattern.
- **Graffiti**: The text "Familia Mendoza Silva" is drawn as graffiti on the ground.
- **Mid-air jump**: When the character is in the air and the user performs another
  jump gesture, the character does an additional jump from its current airborne
  position (double jump), capped at 2 total jumps per airtime.

## Capabilities

### New Capabilities

- `game-background-music`: Continuous background music (GroundTheme.mp3) with
  volume mixing that keeps music below sound-effect levels.
- `game-invincibility-theme`: InvincibilityTheme.mp3 plays when score >= 5 coins.
- `game-lives-system`: 3 lives as visible hearts; collision costs a life; game
  over at 0 lives.
- `game-sky-blocks`: Sky blocks that grant a life (max 3) when touched by the
  jumping character, with a coin sound effect.
- `game-moving-clouds`: Clouds drift leftward to simulate forward motion.
- `game-brick-ground`: Brick-colored ground with a brick pattern.
- `game-graffiti`: Graffiti text "Familia Mendoza Silva" on the ground.
- `game-pose-stability`: Game pauses with a camera-distance warning when pose
  detection degrades.
- `game-mid-air-jump`: When airborne and the user jumps again, the character
  performs an additional jump from its current position (double jump, max 2 per
  airtime).

### Modified Capabilities

- `pose-jump-game`: `LEVEL_INTERVAL` changes from 10 to 5; speed progression tied
  to the new 5-block level cadence. Lives system added; sky blocks added; moving
  clouds added; brick ground added; graffiti added; background music added;
  invincibility theme added; pose stability pause added; mid-air jump added.

## Impact

- **Modified**: `src/game.py` — `LEVEL_INTERVAL` → 5; add lives system, sky blocks,
  moving clouds, brick ground, graffiti, background music, invincibility theme,
  pose stability pause, mid-air jump.
- **Modified**: `src/mario_game.py` — same changes as `game.py`.
- **Modified**: `src/minecraft_game.py` — same changes as `game.py`.
- **Modified**: `src/sound_manager.py` — add background music and invincibility
  theme playback with volume mixing.
- **Modified**: `tests/test_game.py`, `tests/test_mario_game.py`,
  `tests/test_minecraft_game.py` — updated for 5-block intervals, lives, sky
  blocks, clouds, ground, graffiti, music, and pose stability.
- **Modified**: `README.md` — documents new features.
- **No breaking changes** to CLI arguments or camera handling.
