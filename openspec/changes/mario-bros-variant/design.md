## Context

The pose jump game (`src/game.py`) renders a grayscale miniatura stick figure
on a solid black background. Obstacles spawn every 40–90 frames. The existing
game uses `SilhouetteDrawer` in `src/silhouette.py` for rendering, with style
strings like `"head_circle"`, `"body_lines"`, `"blank"` etc. dispatched in
`render_character()`.

The Mario Bros variant reuses the same pose detection pipeline (`Camera`,
`PoseDetector`, `JumpDetector` from `game.py`) but swaps the visual layer for a
Mario Bros aesthetic and restructures obstacle spacing into discrete levels.

Key existing code referenced:
- `JumpDetector` (game.py): detects jumps from shoulder landmark movement (threshold, cooldown, EMA baseline).
- `PlayerCharacter` (game.py): miniatura character with physics (jump velocity + gravity), pose scaling to `CHARACTER_TARGET_HEIGHT`.
- `SilhouetteDrawer` (silhouette.py): rendering methods dispatched by style strings.
- `Obstacle` / `ObstacleManager` (game.py): obstacle spawning, collision, speed progression.

## Goals / Non-Goals

**Goals:**
- Mario Bros aesthetic: sky-blue background, clouds, bushes, brick ground,
  Mario-coloured character (red cap, peach face, red shirt, blue overalls).
- Character still mimics the webcam person's pose and jump (pose-driven miniatura).
- Obstacles more separated at start (level 1: 150–250 frame gaps), tightening
  every 30 obstacles to advance through levels.
- Three Mario obstacle types: pipes, blocks (question blocks), goombas.
- All new code covered by unit tests, no regressions in existing suite.
- Separate launch script (`run_mario.sh`) and entry point (`mario_main.py`).

**Non-Goals:**
- No camera feed in the game view (solid background only, matching taste).
- No facial feature rendering on the character (stick-figure/miniatura approach).
- No pixel-art sprite sheets — rendering uses cv2 primitives (circles, lines,
  ellipses, rectangles) consistent with the existing codebase.
- No modifications to the existing pose jump game or main silhouette app.

## Decisions

### Decision 1: Separate game variant, not integrated into existing game

**Choice:** Create new files (`mario_game.py`, `mario_main.py`, `run_mario.sh`)
rather than adding Mario modes to the existing `game.py`.

**Rationale:** Non-breaking; matches the user's request for "otra version del
juego"; has its own launch script (taste: executable launch scripts preferred).

### Decision 2: Mario palette applied to pose-driven miniatura

**Choice:** Add `draw_mario_head()` and `draw_mario_body()` to
`SilhouetteDrawer` with style strings `"mario_head"` and `"mario_body"`.
`MarioCharacter` uses these styles, reusing `PlayerCharacter`'s pose-scaling
and physics logic.

**Rationale:** Preserves the stick-figure rendering approach the project prefers
while giving it Mario colours. The character's head uses nose position + shoulder
width (same as `draw_head_circle`); the body uses landmark connections split by
region (arms/torus = red shirt, legs = blue overalls).

**Mario palette (BGR):**
| Element    | Color        | BGR          |
|------------|-------------|-------------|
| Face       | Peach       | (200, 200, 255) |
| Cap        | Red         | (0, 80, 255)    |
| Hair       | Brown       | (30, 30, 30)    |
| Shirt      | Red         | (0, 60, 255)    |
| Overalls   | Blue        | (180, 0, 0)     |
| Sky        | Blue        | (235, 206, 135) |
| Pipe       | Green       | (0, 180, 0)     |
| Block      | Orange      | (30, 165, 200)  |
| Goomba     | Red-brown   | (0, 50, 200)    |

### Decision 3: Level-based progressive obstacle spacing

**Choice:** Levels increment every `LEVEL_INTERVAL = 30` obstacles passed. Each
level selects a tighter spawn gap range from `LEVEL_SPAWN_GAP_RANGES`:

| Level | Gap range (frames) |
|-------|-------------------|
| 1     | 150–250           |
| 2     | 120–200           |
| 3     | 100–180           |
| 4     | 80–150            |
| 5+    | 60–120            |

**Rationale:** Level 5+ is capped at the tightest range; the speed progression
(×1.10 every 10 obstacles) continues independently to ramp difficulty.

### Decision 4: Three obstacle types cycled sequentially

**Choice:** `MarioObstacleManager._spawn()` cycles through `OBSTACLE_TYPES =
["pipe", "block", "goomba"]` in order. Each type has fixed dimensions, color,
and variant rendering (blocks show "?", goombas have white eyes).

**Rationale:** Simple, predictable, and visually distinct. Avoids random
selection noise.

### Decision 5: Ground lowered to 85% height

**Choice:** Use `GROUND_Y_RATIO = 0.85` (vs existing `0.80`) so there is more
vertical space for clouds and bushes above the ground.

## Risks / Trade-offs

- **[Risk] Mario character may look too similar to existing stick figure at 90px height.**
  → Mitigation: thicker lines (3px for body), distinct red cap oval above the
  face, and peach face color contrasting with the sky. If visual testing shows
  it doesn't read as Mario, the cap size or color contrast can be tuned.
- **[Risk] Fine limb positions from pose may create odd Mario proportions.**
  → Accepted: the character mimics the person's actual pose, which is the core
  requirement.
- **[Risk] 150–250 frame gaps at level 1 may make the game too easy initially.**
  → Accepted trade-off: the user explicitly requested wider spacing "to be able
  to advance through levels." Difficulty ramps via both level tightening and
  speed multiplication.

## Migration Plan

This is a new, additive feature — no existing code or data is modified in a
breaking way. The only modification to existing files is adding two methods and
two style strings to `SilhouetteDrawer`, which are opt-in (only activated when
`"mario_head"` / `"mario_body"` style strings are passed).

Deployment steps:
1. Add Mario rendering methods to `silhouette.py`.
2. Create `mario_game.py`, `mario_main.py`, `run_mario.sh`.
3. Add tests.
4. Update README.

Rollback: delete the new files and revert the two added methods + style strings
in `silhouette.py`.

## Open Questions

- Whether to add a background music / sound effects (requires new dependency,
  e.g. `pygame.mixer` — already installed via `pygame`). Deferred to a later
  iteration; the current variant is visual-only.
