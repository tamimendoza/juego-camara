## Context

The `SilhouetteDrawer` in `src/silhouette.py` renders characters via style tokens
listed in `MimicCharacter.STYLES` (`src/character.py`). Each token maps to a
drawing layer in `render_character()`. Existing styles cycle through five
presets (Style 0–4). See proposal.md for motivation.

The new Style 5 requires two new drawing layers (`head_circle`, `body_lines`)
and a new style entry.

## Goals / Non-Goals

**Goals:**
- Add `draw_head_circle()` — one filled circle at the nose position, radius ∝ shoulder width
- Add `draw_body_lines()` — skeleton lines for body landmarks (≥ 11) only, excluding face connections
- Register Style 5 in `MimicCharacter.STYLES` as `["blank", "head_circle", "body_lines"]`
- Add unit tests for both new methods

**Non-Goals:**
- Changing face landmark handling for existing styles
- Adding new pose detection or smoothing logic
- Making head circle color or body line color configurable (use existing `joint_color` / `line_color`)

## Decisions

### Decision 1: Head circle geometry

**Choice:** Center the circle at landmark 0 (nose). Compute radius as `max(shoulder_width * 0.25, 10)` where `shoulder_width = distance(landmark 11, landmark 12)`.

**Rationale:** The nose is the most reliably tracked face landmark. Using shoulder width as a scale reference makes the circle resize naturally with the user's distance from the camera. A 0.25 factor gives a head proportion that looks balanced against the body lines. The `10` minimum ensures a visible circle when shoulders are far apart.

**Alternatives considered:**
- Face landmark centroid as center: less stable than nose when face is partially occluded
- Fixed pixel radius: does not scale with user distance

### Decision 2: Body line filtering

**Choice:** In `draw_body_lines()`, iterate `POSE_CONNECTIONS` and skip any connection where either endpoint index is < 11 (i.e., involves a face landmark).

**Rationale:** MediaPipe's `POSE_CONNECTIONS` includes face connections (eyes, mouth). Filtering at index 11 cleanly separates body from face without maintaining a separate connection list. The same face/body boundary (index 11) is already used implicitly in the codebase (e.g., `LIMB_TRIANGLES` starts at index 11).

**Alternatives considered:**
- Hardcoded body connection list: more explicit but duplicates POSE_CONNECTIONS and must be kept in sync
- Filter in `render_character`: couples style dispatch with connection filtering; better to encapsulate in the drawing method

### Decision 3: Style token design

**Choice:** New tokens `head_circle` and `body_lines` follow the same string-token pattern as `mask`, `polygons`, `skeleton`, `joints`, `dark`, `blank`.

**Rationale:** Consistent with the existing architecture — `render_character()` dispatches on string tokens in `styles` list. No structural change needed.

## Risks / Trade-offs

- **[Risk] Nose landmark may be None when face is not visible.** → Mitigation: `draw_head_circle` checks for None and skips drawing if the nose or both shoulders are unavailable.
- **[Risk] Face connections may still appear if POSE_CONNECTIONS changes in a MediaPipe version.** → Mitigation: filtering by index ≥ 11 is version-independent since landmark 11 (left shoulder) has been stable since MediaPipe Pose's first release.
- **[Trade-off] Head circle color is hardcoded to `joint_color` (white).** → Acceptable for MVP; could be made configurable later via `BODY_COLORS`.
