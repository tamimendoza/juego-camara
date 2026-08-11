## Why

The existing Mario Bros pose jump game renders the player's webcam person as a
small Mario-styled miniatura character with a peach face circle, red cap, and
brown hair arc. The user wants to replace Mario's head entirely with the
person's **real face** captured from the camera — showing only the face (no cap,
no hair, no stylized circle) while keeping the Mario body lines (red shirt for
arms/torus, blue overalls for legs) and all existing game mechanics.

This requires adding MediaPipe FaceMesh (468 face landmarks) alongside the
existing PoseLandmarker pipeline, cropping the face from the camera frame, and
overlaying it at the character's head position.

## What Changes

- **Add `src/face_detector.py`** — `FaceDetector` class wrapping
  `mediapipe.solutions.face_mesh` for 468-point face landmark detection.
- **Add `src/face_crop.py`** — `FaceCropper` class that extracts a circular
  face region from the BGR camera frame using FaceMesh contour landmarks.
- **Add `draw_face_overlay()` to `SilhouetteDrawer`** (`src/silhouette.py`) —
  overlays a cropped face image at the nose landmark position, using the same
  head-radius calculation as `draw_mario_head()`.
- **Add `"face_overlay"` style** to `render_character()` dispatch in
  `src/silhouette.py`.
- **Create `src/mario_face_game.py`** — `MarioFaceCharacter` (inherits
  `MarioCharacter` physics, replaces head rendering with face overlay) and
  `MarioFaceGameEngine` (extends `MarioGameEngine`, adds FaceMesh + FaceCropper
  to the pipeline).
- **Create `src/mario_face_main.py`** — entry point mirroring `mario_main.py`
  but with FaceMesh detection and face crop passing.
- **Create `run_mario_face.sh`** — launch script mirroring `run_mario.sh`.
- **Add tests** in `tests/test_mario_face_game.py` and
  `tests/test_silhouette.py`.
- **Update `README.md`** with a "Mario Face Game" section.

## Capabilities

### New Capabilities

- `mario-face-capture`: A Mario Bros-themed pose jump game variant where the
  player's real face (captured from the webcam via MediaPipe FaceMesh) replaces
  the Mario head entirely. The character still mimics the player's pose and jump
  via PoseLandmarker body landmarks, but the head is a real face crop instead of
  a peach face circle + cap + hair arc.

### Modified Capabilities

- `pose-jump-game` rendering: `SilhouetteDrawer` gains `draw_face_overlay()`
  method and a new `"face_overlay"` style string in `render_character()`. No
  existing rendering behaviour is changed.

## Impact

- **New**: `src/face_detector.py` — FaceMesh wrapper.
- **New**: `src/face_crop.py` — Face cropping utility.
- **Modified**: `src/silhouette.py` — adds `draw_face_overlay()` method and
  `"face_overlay"` style string (additive, opt-in).
- **New**: `src/mario_face_game.py` — Mario face character + game engine.
- **New**: `src/mario_face_main.py` — entry point.
- **New**: `run_mario_face.sh` — launch script.
- **New**: `tests/test_mario_face_game.py` — unit tests.
- **Modified**: `tests/test_silhouette.py` — adds face overlay rendering tests.
- **Modified**: `README.md` — documents the new Mario Face Game mode.
- **New**: `openspec/changes/mario-face-capture/` — OpenSpec change artifacts.
