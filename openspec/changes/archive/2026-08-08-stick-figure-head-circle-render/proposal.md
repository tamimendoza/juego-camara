## Why

The current stick-figure style (Style 4 `blank` + `skeleton` + `joints`) still shows the camera feed as a black background with all 33 landmarks drawn as joint dots and all face connections as lines. Users want a cleaner rendering that hides the person entirely (solid background) and represents the head with a single circle while drawing the rest of the body as lines only.

## What Changes

- Add a new rendering style (`blank` + `head_circle` + `body_lines`) that:
  - Fills the frame with a solid black background (no camera feed, no person visible)
  - Draws a single filled circle representing the head, positioned at the nose landmark with a radius proportional to shoulder width
  - Draws lines connecting only body landmarks (indices 11–32), excluding face connections
- Add two new rendering-layer methods to `SilhouetteDrawer`: `draw_head_circle()` and `draw_body_lines()`
- Register the new style as Style 5 in `MimicCharacter.STYLES`
- Update `SilhouetteDrawer.render_character()` to handle the `head_circle` and `body_lines` style tokens
- Update `README.md` to document Style 5
- Add unit tests for the new rendering methods

## Capabilities

### New Capabilities

*(none)*

### Modified Capabilities

- `camera-pose-silhouette`: A new rendering style is added that draws a circle for the head and lines for the body on a solid black background, hiding the person entirely.

## Impact

- **src/silhouette.py** — `SilhouetteDrawer`: add `draw_head_circle()`, `draw_body_lines()`, and handle new style tokens in `render_character()`
- **src/character.py** — `MimicCharacter.STYLES`: add Style 5 with `["blank", "head_circle", "body_lines"]`
- **README.md** — document the new Style 5 rendering mode
- **tests/test_silhouette.py** — new unit tests for `draw_head_circle()` and `draw_body_lines()`
- No changes to pose detection, camera capture, smoothing, or mirror logic
