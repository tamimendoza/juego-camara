## Why

Today the character jumps whenever the player's shoulders rise above a baseline,
so raising the arms, shrugging, or walking closer to the camera produces
unwanted jumps. A real jump starts by bending the legs, so the jump gesture
should be gated on the legs. Additionally, the in-game character renders its
torso as an empty outline (a "hole in the chest"), the game window can be
resized/zoomed freely, and an airborne double jump can push the character off
the top of the screen.

## What Changes

- **Leg-driven two-phase jump detection**: the character jumps only after the
  player *bends the legs* (crouch) **and then** performs an actual jump (body
  rises / legs extend). Raising the shoulders alone no longer triggers a jump.
- **Double jump gated on legs**: the mid-air second jump now also requires the
  two-phase leg signal (tuck legs while airborne, then extend/rise), instead of
  a bare shoulder rise.
- **Solid torso fill**: the miniatura character's torso quadrilateral is filled
  with a solid color (character color in the base game, red shirt in the Mario
  / Mario Face variants) so the chest no longer looks hollow. Minecraft is
  unaffected (its torso is already a filled voxel block).
- **No zoom on the game screen**: the four game windows are created with a
  fixed size (`cv2.WINDOW_AUTOSIZE`), so they cannot be resized/zoomed.
- **Jump clamped to the visible area**: the character's jump (including the
  double jump) is clamped so the whole character always stays inside the
  visible game area and never leaves the top/bottom of the screen.

## Capabilities

### New Capabilities

- `game-window-fixed-size`: the game display windows (base game, Mario Bros,
  Minecraft Mario, Mario Face) are fixed-size and cannot be resized or zoomed.

### Modified Capabilities

- `pose-jump-game`: jump detection now requires the two-phase leg signal
  (crouch then jump) instead of a shoulder rise; the character renders a
  solidly filled torso; the character never leaves the visible area while
  jumping.
- `game-mid-air-jump`: the double jump is now gated on the two-phase leg signal
  while airborne, and its height is capped so the character stays on screen.
- `mario-bros-variant`: jump detection follows the same two-phase leg signal;
  the Mario character renders a solidly filled red torso; the character never
  leaves the visible area while jumping.
- `mario-face-capture`: jump detection follows the same two-phase leg signal
  (shared `JumpDetector`); the character renders a solidly filled red torso;
  the character never leaves the visible area while jumping.
- `mario-minecraft-character`: jump detection follows the same two-phase leg
  signal (shared `JumpDetector`); the character never leaves the visible area
  while jumping. Torso rendering is unchanged (already filled voxel blocks).

## Impact

- `src/game.py` — `JumpDetector` two-phase logic; `PlayerCharacter` torso fill
  style + jump clamp; shared constants.
- `src/mario_game.py` — `MarioCharacter` torso fill + jump clamp.
- `src/mario_face_game.py` — `MarioFaceCharacter` torso fill (inherits clamp).
- `src/minecraft_game.py` — `MinecraftMarioCharacter` jump clamp (jump
  detection comes from the shared `JumpDetector`).
- `src/silhouette.py` — new `"torso_fill"` rendering layer.
- `src/game_main.py`, `src/mario_main.py`, `src/minecraft_main.py`,
  `src/mario_face_main.py` — fixed-size window (no zoom).
- Tests: `tests/test_game.py`, `tests/test_mario_game.py`,
  `tests/test_mario_face_game.py`, `tests/test_minecraft_game.py`,
  `tests/test_silhouette.py`.
- `README.md` — updated control/gameplay docs.
