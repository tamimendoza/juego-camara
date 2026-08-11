## Context

The pose jump game (`src/game.py`) renders a grayscale miniatura stick figure on
a solid black background. The `mario-bros-variant` change added a Mario Bros
aesthetic using smooth cv2 primitives (circle head, ellipse cap, line body) with
a sky-blue background and themed obstacles (pipes, blocks, goombas).

The `SilhouetteDrawer` in `src/silhouette.py` dispatches style strings in
`render_character()` to drawing methods. Existing Mario styles are
`"mario_head"` (circle face + ellipse cap) and `"mario_body"` (line body with
red/blue colors).

A Minecraft-style Mario character replaces the smooth primitives with
**rectangular blocks (voxels)** — the defining visual feature of Minecraft's
Steve/Alex player model. Each body part is a thick filled rectangle instead of
a thin line, giving the character a pixelated, blocky appearance.

Reference data retrieved from the official Minecraft Wiki (`/w/Steve`):
> Steve is typically depicted with wide arms, brown skin, short dark brown hair,
> a visible nose, dark purple eyes, and a beard. Signature features: a cyan shirt
> with noticeable cuffs, untucked on the left-hand side. Gray shoes and dark blue
> pants.

For a Minecraft-style Mario, we blend this with Mario's palette: **red cap,
peach face, red shirt, blue overalls** — but rendered as rectangular voxel
blocks instead of smooth circles/lines.

## Goals / Non-Goals

**Goals:**
- Minecraft/voxel aesthetic: render the Mario miniatura as rectangular blocks
  (cv2.rectangle) instead of circles/ellipses/lines, with thick borders to
  emphasize the "block" look.
- Mario color palette preserved: red cap block, peach face block, red shirt
  blocks for arms/torso, blue overalls blocks for legs.
- Pixelated eyes on the face block (two small black rectangles + optional nose).
- Minecraft-themed background: sky-blue fill, pixel-style white clouds, grass-
  block ground band (green top + brown dirt sides).
- Pose-driven: the blocky character still mirrors the player's actual pose and
  jump via scaled landmark transformation (reuses `MarioCharacter._update_render_points`).
- Three obstacle types cycled sequentially (pipe, block, goomba), voxel-style
  rectangles, same level/speed progression as the Mario variant.
- Separate launch script (`run_minecraft.sh`) and entry point
  (`minecraft_main.py`), mirroring the Mario variant pattern.

**Non-Goals:**
- No camera feed in game view (solid background only, matching project taste).
- No 3D voxel rendering (the project uses 2D cv2 primitives only).
- No pixel-art sprite sheets — rendering uses cv2 rectangles consistent with the
  existing codebase.
- No modifications to the existing Mario Bros variant or the base pose jump game.
- No new dependencies (uses existing cv2, numpy, pygame).

## Decisions

### Decision 1: Separate game variant, not a style mode in the main app

**Choice:** Create new files (`minecraft_game.py`, `minecraft_main.py`,
`run_minecraft.sh`) rather than adding Minecraft styles to the main `main.py`
style cycling or reusing `mario_game.py`.

**Rationale:** Non-breaking; mirrors the `mario-bros-variant` pattern of a
parallel game variant. Has its own launch script (taste: executable launch
scripts preferred). The Minecraft rendering styles are still added to
`SilhouetteDrawer` so they could be reused elsewhere.

### Decision 2: Blocky rectangle rendering via new SilhouetteDrawer methods

**Choice:** Add `draw_minecraft_head()` and `draw_minecraft_body()` to
`SilhouetteDrawer` with style strings `"minecraft_head"` and
`"minecraft_body"`.

- **Head:** A square block centered at the nose landmark (index 0), sized by
  shoulder width. The top ~40% is filled red (cap), the bottom ~60% is filled
  peach (face). Two small black pixel rectangles for eyes. A 2px black border
  outlines the entire block for the voxel look.

- **Body:** Five **predefined solid rectangle segments** (not connection-based
  line segments). Each limb is a single filled rectangle spanning from joint to
  joint end:
  - Torso: rectangle from shoulder midpoint to hip midpoint — red (shirt).
  - Left arm: rectangle from left shoulder (11) to left wrist (15) — red.
  - Right arm: rectangle from right shoulder (12) to right wrist (16) — red.
  - Left leg: rectangle from left hip (23) to left ankle (27) — blue (overalls).
  - Right leg: rectangle from right hip (24) to right ankle (28) — blue.
  Each rectangle is thick (~7px) with a 1px darker border to simulate the
  voxel/block edge. The rectangles are drawn directly from predefined landmark
  indices — NOT by iterating over `connections` (which would produce 3+ separate
  thin rectangles per limb and look like connected line-segments rather than
  solid Minecraft blocks).

**Rationale:** Solid single-rectangle-per-limb blocks produce the unmistakable
Minecraft "voxel" look — each arm and leg is one solid cube, not a chain of
smaller rectangles. The rectangle orientation follows the pose landmarks, so
the character still mimics the player's pose.

### Decision 6: Character does not enlarge ("ampliarse") on partial pose; remains still when undetected

**Choice:** The Minecraft Mario character uses a **pose-height-based scale
capped by `MAX_SCALE`** to prevent enlargement. The scale is computed as
`CHARACTER_TARGET_HEIGHT / pose_height`, then clamped to `MAX_SCALE`
(≈0.55). This means:

- When the full body is detected (typical pose height ≈ 210–260 px in 640×480),
  the character renders at ~`CHARACTER_TARGET_HEIGHT` (110 px) — its normal size.
- When only partial landmarks are visible (e.g. user far from camera, or
  shoulders/arms detected but legs occluded), the pose height is smaller,
  which would normally push the scale above `MAX_SCALE`. The cap prevents the
  character from **ampliarse** (growing larger than normal) — instead the
  character stays at its normal size or shrinks slightly.
- When no pose is detected at all, the character shows a static rest-pose
  **fallback** (the `render()` path when `_render_points is None`).
- When pose quality degrades mid-stream (e.g. landmark dropout to fewer than
  `min_visible = 5` visible points), `update()` does **not** call
  `_update_render_points()` at all, so the character **keeps its last known
  pose** — it "remains quieto" rather than jumping or morphing.

**Rationale:** This addresses the explicit requirement that the character
"no debe ampliarse" (must not enlarge) and "debe permanecerse quieto hasta
que el usuario sea detectado correctamente" (should remain still until
detected correctly). A completely fixed scale factor would make the character
size depend on raw pixel coordinates (varying with camera resolution and user
distance), so the capped pose-height approach is used instead.

**Rationale:** Minecraft characters are inherently fixed-size voxels. Scaling
would break the voxel aesthetic and make the character look distorted. A fixed
size also makes collision detection more predictable.

**Minecraft palette additions (BGR):**
| Element    | Color        | BGR          |
|------------|-------------|-------------|
| Sky        | Blue        | (235, 206, 135) |
| Grass top  | Green       | (0, 160, 60)  |
| Grass side | Dirt brown  | (100, 80, 40) |
| Dirt       | Brown       | (80, 60, 30)  |
| Cloud      | White       | (255, 255, 255) |
| Block border | Dark gray | (20, 20, 20) |

Mario palette (reused from existing constants):
| Element    | Color        | BGR          |
|------------|-------------|-------------|
| Face       | Peach       | (200, 200, 255) |
| Cap        | Red         | (0, 80, 255)    |
| Hair       | Brown       | (30, 30, 30)    |
| Shirt      | Red         | (0, 60, 255)    |
| Overalls   | Blue        | (180, 0, 0)     |

### Decision 3: Rectangle orientation helper

**Choice:** Add a helper `_draw_oriented_rect(frame, p1, p2, width, color)`
that computes the rectangle vertices perpendicular to the line from p1 to p2.
This produces a "thick line as rectangle" that looks like a Minecraft limb
block.

**Rationale:** Each limb block needs to be oriented along the limb direction
with a fixed pixel width. This helper is reused for all four limbs.

### Decision 4: Reuse level/speed progression from Mario variant

**Choice:** `MinecraftObstacleManager` mirrors `MarioObstacleManager` exactly
— same `LEVEL_SPAWN_GAP_RANGES`, `LEVEL_INTERVAL = 30`, same speed multiplier
(×1.10 every 10 obstacles), same 3-obstacle type cycling.

**Rationale:** No need to redesign gameplay mechanics; the novelty is purely
visual (Minecraft rendering + background). Keeps the plan focused.

### Decision 5: Ground as grass block band

**Choice:** `GROUND_Y_RATIO = 0.85` (same as Mario variant). The ground band
is drawn as two stacked rectangles: a green top strip (grass) over a brown
dirt strip, with a thin darker-brown border to simulate block texture.

**Rationale:** Gives the Minecraft "grass block" look without sprite sheets.

## Risks / Trade-offs

- **[Risk] Oriented rectangles may look distorted at extreme pose angles.**
  → Mitigation: cap the rectangle width at a reasonable size relative to
  shoulder width; if the limb vector is too short (< 5px), skip drawing it.
- **[Risk] Blocky character at 90px height may be too small to read as Mario.**
  → Mitigation: increase `CHARACTER_TARGET_HEIGHT` to 110px for the Minecraft
  variant, and use thicker rectangle outlines (BLOCK_BORDER_WIDTH = 2) for
  better visibility against the sky background.
- **[Risk] Rectangle orientation math may produce degenerate geometry.**
  → Mitigation: unit-test `_draw_oriented_rect` with vertical, horizontal, and
  diagonal limb vectors; clamp minimum rectangle width to 4px.
- **[Risk] Player may not immediately recognize the Minecraft Mario aesthetic.**
  → Accepted: the red cap block + peach face + red/blue body blocks are
  distinctively Mario, and the blocky rectangles + grass-block ground clearly
  evoke Minecraft. Visual tuning of cap/face split ratio can be adjusted.

## Migration Plan

This is a new, additive feature — no existing code or data is modified in a
breaking way. The only modification to existing files is adding two methods and
two style strings to `SilhouetteDrawer` (in `silhouette.py`), which are opt-in.

Deployment steps:
1. Add Minecraft color constants + helper + drawing methods to `silhouette.py`.
2. Wire `"minecraft_head"` / `"minecraft_body"` into `render_character()`.
3. Create `minecraft_game.py`, `minecraft_main.py`, `run_minecraft.sh`.
4. Add tests.
5. Update README.

Rollback: delete the new files and revert the added methods + style strings in
`silhouette.py`.

## Open Questions

- Whether to add Minecraft-style mob obstacles (e.g., green Creeper) as
  additional obstacle types. **Decision: deferred to a later iteration** — the
  initial variant reuses the Mario obstacle types (pipe, block, goomba) but
  rendered as voxel rectangles.
- Whether to add background parallax (ground scrolls slower than obstacles for
  depth). **Decision: deferred** — single-layer background for initial version.
