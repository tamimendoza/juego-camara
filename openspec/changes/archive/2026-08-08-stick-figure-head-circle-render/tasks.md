## 1. New Rendering Methods

- [x] 1.1 Implement `draw_head_circle()` in `SilhouetteDrawer` — circle at nose landmark, radius ∝ shoulder width
- [x] 1.2 Implement `draw_body_lines()` in `SilhouetteDrawer` — draw connection lines for body landmarks only (indices ≥ 11)
- [x] 1.3 Add `head_circle` and `body_lines` token handling in `render_character()`

## 2. New Rendering Style

- [x] 2.1 Add Style 5 (`["blank", "head_circle", "body_lines"]`) to `MimicCharacter.STYLES`

## 3. Documentation

- [x] 3.1 Update `README.md` with Style 5 description in the Controls section

## 4. Testing

- [x] 4.1 Write unit tests for `draw_head_circle()` in `tests/test_silhouette.py`
- [x] 4.2 Write unit tests for `draw_body_lines()` in `tests/test_silhouette.py`
- [x] 4.3 Run `pytest tests/` — all tests pass
