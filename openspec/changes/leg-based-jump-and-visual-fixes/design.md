## Context

See `proposal.md` — Why for motivation.

Current state that shapes the approach:

- A single `JumpDetector` class lives in `src/game.py` and is reused by all four
  game engines (`game.py`, `mario_game.py`, `mario_face_game.py`,
  `minecraft_game.py`). It currently fires whenever the shoulder midpoint rises
  ≥ 30 px above an EMA baseline.
- Each game engine's `_update_playing` mirrors the pose (`mirror_points`), calls
  `_player.update(...)`, then `if jump_detector.update(landmarks): player.jump()`.
  `player.jump()` independently enforces `MAX_JUMPS` (double jump) and the
  airborne state, so the detector only decides *whether* a jump gesture
  happened — it is airborne-agnostic. This lets the same two-phase logic drive
  both the ground jump and the mid-air double jump without engine changes.
- Characters render through `SilhouetteDrawer.render_character` with a styles
  list: base game uses `["head_circle", "body_lines"]`, Mario/Mario Face use
  `["mario_head", "mario_body"]` / `["mario_body", "face_overlay"]`, Minecraft
  uses `["minecraft_head", "minecraft_body"]`. The torso is currently drawn only
  as outline lines.
- All four game windows are created with `cv2.namedWindow(..., cv2.WINDOW_NORMAL)`,
  which lets the user resize (and effectively zoom) the game display.
- Jump physics: `_jump_offset` (negative = above ground), `GRAVITY`, initial
  `JUMP_VELOCITY = -14`, double jump adds `DOUBLE_JUMP_VELOCITY = -10`
  (combined `vy = -24` → uncapped apex ≈ 480 px, off-screen).

## Goals / Non-Goals

**Goals:**
- A single, shared two-phase jump detector so all four games behave identically
  with the leg gesture.
- Keep the detector airborne-agnostic so the mid-air double jump reuses it.
- Minimal rendering surface changes: one new drawing layer reused by the three
  character styles that draw a hollow torso.
- Deterministic, testable jump clamping via physics (not per-frame render
  jitter).

**Non-Goals:**
- No changes to the standalone silhouette app (`src/main.py`, `main.py` window).
- No new external dependencies.
- No redesign of pose detection or game physics beyond the jump clamp.

## Decisions

### D1 — Extend the shared `JumpDetector` with a two-phase state machine

Keep the class name and constructor (`threshold`, `cooldown`, `ema_alpha`) and
add an internal state machine: `IDLE` → `ARMED` → fire → cooldown.

- **IDLE**: continuously updates the shoulder EMA baseline (as today). A jump
  can never fire here.
- **ARM**: when both knee angles (hip–knee–ankle, landmarks 23/25/27 and
  24/26/28) are below `CROUCH_ANGLE_THRESHOLD` for `CROUCH_HOLD_FRAMES`
  consecutive frames, capture the shoulder baseline and enter `ARMED`. The arm
  state expires after `ARMED_TIMEOUT_FRAMES` if no jump happens.
- **Fire**: while `ARMED`, fire when the player actually leaves the ground:
  both the shoulder midpoint **and** the ankle midpoint rise above the crouch
  baseline by their thresholds. Then start the existing cooldown.

Rationale: keeping the same class avoids touching all four engines and their
tests' imports. Requiring *both* shoulders and ankles to rise rejects the
"crouch then just stand up" case — standing up lifts the shoulders but keeps
the feet planted, so the ankles do not rise. This is what distinguishes a real
jump ("efectivamente realiza un salto") from a posture change.

Alternatives considered:
- Fire on shoulder rise only while armed → false fires when the player squats
  and stands up quickly (shoulders rise ≥ 30 px).
- Velocity-based discriminator (shoulder rise per frame) → more tunable but
  less robust than requiring whole-body translation (ankles rising).

### D2 — Crouch metric: average knee bend angle

Crouch is measured as the average of both knee angles (degrees at landmarks
25 and 26). Standing straight ≈ 180°, a bent/tilted leg drops below
`CROUCH_ANGLE_THRESHOLD` (start at 150°). Both legs must be bent to arm.

Rationale: the knee angle directly captures "inclina las piernas". Alternatives
considered: hip-to-knee vertical distance (thigh compression) and hip-to-ankle
distance; both are more sensitive to distance-to-camera and body proportions,
whereas the angle is scale-invariant.

### D3 — New `"torso_fill"` drawing layer in `SilhouetteDrawer`

Add a `torso_fill` style to `render_character` that fills the torso
quadrilateral (`get_visible_polygon(points, [11, 12, 24, 23])`) with
`self.silhouette_color` using `cv2.fillPoly`. It is drawn right after the
segmentation-mask layer and before skeleton/lines so the outline lines render
on top.

- Base game `PlayerCharacter.render`: styles become
  `["torso_fill", "head_circle", "body_lines"]`.
- `MarioCharacter.render`: `["torso_fill", "mario_head", "mario_body"]`.
- `MarioFaceCharacter.render`: `["torso_fill", "mario_body", "face_overlay"]`
  (and `["torso_fill", "mario_head", "mario_body"]` on face fallback).
- The `silhouette_color` is already set to the character color (base game) and
  to `MARIO_SHIRT` (Mario), so no palette changes are needed.

Minecraft is untouched: `minecraft_body` already fills the torso with a solid
voxel block.

Rationale: one shared layer reused by three characters beats duplicating torso
filling in each `render()`. Alternatives considered: reusing the `"polygons"`
style — rejected, it fills the head and limbs with a fixed pastel palette, not
the character color.

### D4 — Clamp the jump apex in physics

In each character's `update()`, clamp `_jump_offset` so the character never
leaves the visible area:

```
MAX_JUMP_OFFSET = ground_y - TOP_MARGIN - CHARACTER_TARGET_HEIGHT
if _jump_offset < -MAX_JUMP_OFFSET:  # more negative than allowed
    _jump_offset = -MAX_JUMP_OFFSET
    _vy = 0.0
```

`TOP_MARGIN = 10` px. Applied in `PlayerCharacter`, `MarioCharacter`, and
`MinecraftMarioCharacter` (Mario Face inherits from `MarioCharacter`).

Rationale: capping the physics quantity is deterministic and testable (unit
tests can assert the apex). Clamping render points per-frame was rejected — it
produces visible jitter because the pose's topmost landmark changes with arm
position.

The clamp still satisfies the "clears every obstacle height" requirement: the
base game's max obstacle is 120 px tall and requires a 140 px apex, while the
capped apex is ≈ 284 px (384 − 10 − 90).

### D5 — Fixed-size game windows

Replace `cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)` with
`cv2.WINDOW_AUTOSIZE` in `game_main.py`, `mario_main.py`, `minecraft_main.py`,
and `mario_face_main.py`. This locks the window to the native 640×480 image and
disables user resizing/zooming.

Rationale: `WINDOW_AUTOSIZE` is the standard HighGUI flag for a non-resizable
display. `main.py` (the standalone silhouette app) is intentionally left alone
per Non-Goals.

## Risks / Trade-offs

- [Jump becomes harder to trigger] Players must learn to crouch before every
  jump. → Mitigation: thresholds are exposed as module constants for tuning;
  the crouch hold is short (4 frames) so a natural jump's down-up motion arms
  it on its own.
- [False fire on fast "squat then stand up"] Standing up still lifts shoulders.
  → Mitigation: the ankle-rise condition (D1) requires the feet to leave the
  ground; if it proves too strict, relax to a velocity check on the shoulders.
- [Capped double jump reduces air time] Clearing tall obstacles is still safe
  (apex ≈ 284 px vs 140 px needed) but the double jump feels flatter. →
  Mitigation: keep `JUMP_VELOCITY`/`DOUBLE_JUMP_VELOCITY` tunable; raise
  `TOP_MARGIN` cap only if the screen layout allows.
- [Shared detector change touches all four games at once] A regression in
  `JumpDetector` affects every variant. → Mitigation: the game-level tests
  (`test_game.py`, `test_mario_game.py`, `test_mario_face_game.py`,
  `test_minecraft_game.py`) all get updated in the same change; the detector
  tests are the single source of truth for the gesture logic.
- [`WINDOW_AUTOSIZE` behavior varies by backend] On some Qt builds the window
  still allows wheel-scroll zoom. → Mitigation: verify on the target Ubuntu;
  if needed, follow up with a backend-specific fix.

## Migration Plan

This is a self-contained, single-repo change with no external systems.
Deployment is a normal commit:

1. Implement the detector, torso fill, clamp, and window flag together (they
   share test files).
2. Update all affected unit tests and the README controls section.
3. Run the full pytest suite; manually verify each game mode with the webcam.
4. Rollback is a single revert of the change commit — no data migration.

## Open Questions

None that would change the specs, approach, or task breakdown.
