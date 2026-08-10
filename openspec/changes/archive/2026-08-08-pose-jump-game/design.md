## Context

The `src/character.py` `CharacterManager` manages multi-person pose-driven
silhouettes with styles, mirror mode, and live rendering via `SilhouetteDrawer`
in `src/silhouette.py`. The `SilhouetteDrawer` already supports a
`head_circle` + `body_lines` rendering style (Style 5), which draws a circle
for the head and lines for body landmarks only (indices >= 11), excluding all
face connections. This matches the user's preference for de-identified
stick-figure rendering on a solid background.

The game reuses the pose detection pipeline (`Camera` → `PoseDetector` →
landmark extraction) but replaces the output stage: instead of rendering a
full-size silhouette that mimics the user, it renders a small "miniatura"
character at a fixed screen position and uses pose data for jump input rather
than pose-to-screen coordinate mapping.

## Goals / Non-Goals

**Goals:**
- Detect jumps from real-time pose: shoulder midpoint (landmarks 11 & 12)
  rises above a dynamic EMA baseline by at least 50 px
- Render a miniatura character using scaled-transformed pose landmarks
  (head circle + body lines only, no face connections, solid black background)
- Spawn obstacles from the right edge at a base speed; move leftward
- Increase game speed ×1.10 every 10 obstacles cleared
- End game on AABB collision between character and obstacle
- States: MENU (press SPACE to start) → PLAYING → GAME_OVER (press SPACE to restart)

**Non-Goals:**
- Multi-person support in game mode (single player only for MVP)
- Power-ups, lives, or difficulty settings beyond speed progression
- Audio / sound effects
- Score persistence or high-score tracking
- Ducking or crouching mechanics (jump-only for MVP)

## Decisions

### Decision 1: Jump detection via shoulder midpoint y-position

**Choice:** Track the average y-coordinate of left shoulder (11) and right
shoulder (12). Maintain a dynamic baseline using EMA (alpha=0.05) of the
shoulder y when the jump detector is not in cooldown. Trigger a jump when
`shoulder_y < baseline - 50px`. Cooldown of 15 frames prevents double-trigger.

**Rationale:** Shoulders are the most stable body landmarks for detecting
whole-body vertical displacement. The nose moves when the head tilts; hips may
be occluded by the body. A dynamic EMA baseline handles the player moving
closer or farther from the camera during play. A 50px threshold is large
enough to avoid false positives from pose jitter but small enough to detect
natural jumps.

**Alternatives considered:**
- Nose landmark only: rejected — too sensitive to head tilting
- World landmarks (3D y): rejected — adds complexity, world landmark stability
  varies with MediaPipe version
- Hip landmarks (23, 24): rejected — may be occluded when legs are together

### Decision 2: Miniatura rendering via pose landmark scaling

**Choice:** Transform the player's 33 pose landmarks by: centering on the
shoulder midpoint, scaling to a fixed character height (~90px), and translating
to `(CHARACTER_X, ground_y)`. Render using `SilhouetteDrawer.render_character`
with `["blank", "head_circle", "body_lines"]` token set — the same Style 5 used
by the mimic mode, consistent with taste preference.

**Rationale:** Scaling the actual pose landmarks means the miniatura's
arm/leg positions mimic the player's real pose, making it a true "miniatura de
la persona." Reusing `SilhouetteDrawer` avoids duplicating drawing logic. The
solid black background ("blank") fully de-identifies the camera feed.

**Alternatives considered:**
- Static stick-figure that doesn't move limbs: simpler but less "miniatura-like"
- Full silhouette mask: rejected — taste prefers stick-figure with no face,
  no camera feed

### Decision 3: Speed progression formula

**Choice:** `speed = BASE_SPEED * (SPEED_MULTIPLIER ** (passed_count // 10))`
where `SPEED_MULTIPLIER = 1.10`. Speed is recomputed every frame and applied
to all existing obstacles (not just new ones) via `ObstacleManager.set_speed`.

**Rationale:** Exponential progression (×1.10 per tier) gives a smooth but
noticeable acceleration curve that gets challenging at higher tiers. Applying
to existing obstacles keeps the game feel consistent (no sudden jumps in
individual obstacle speed). Recomputing from the formula every frame makes the
speed a pure function of score — easy to test and reason about.

**Alternatives considered:**
- Linear increment (`+1 px/frame`): too slow to feel like it ramps up
- Speed affects spawn rate too: adds complexity; spawn interval can stay
  roughly constant because increased speed naturally reduces gap time
- Only new obstacles get new speed: feels inconsistent when old slow
  obstacles linger

### Decision 4: Separate game entry point vs. mode toggle in main.py

**Choice:** Create `src/game_main.py` + `run_game.sh` as a separate entry
point, rather than adding a mode toggle to `main.py`.

**Rationale:** The game loop's update logic (gravity, collision, scoring) is
incompatible with `CharacterManager`'s mimic logic. A separate entry point
keeps `main.py` focused on its existing purpose and follows the project's
preference for launch scripts as the primary run method.

## Risks / Trade-offs

- **[Risk] Jump detection false positives from pose noise.** → Mitigation: EMA
  baseline smoothing + 15-frame cooldown. Can be tuned by adjusting threshold.
- **[Risk] Person walks closer/farther from camera, changing shoulder y.** →
  Mitigation: dynamic EMA baseline adapts to gradual position changes.
- **[Risk] Landmark 11 or 12 not visible (person at edge of frame).** →
  Mitigation: JumpDetector returns False when shoulders are None; the
  character simply stays on the ground.
- **[Risk] Collision hitbox feels unfair.** → Mitigation: Player bbox is
  derived from transformed pose bounds (shoulder width + full pose height),
  giving a natural hitbox that scales with the player's detected size.
- **[Trade-off] Obstacle heights are random but not varied in type.** →
  Acceptable for MVP; can add flying obstacles (duck) later.
