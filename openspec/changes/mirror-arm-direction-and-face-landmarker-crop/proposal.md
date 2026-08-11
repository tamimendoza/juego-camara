## Why

Two issues affect the pose camera application:

1. **Mirror mode reverses arm direction**: The current `mirror_points()` function
   performs a pure X-axis flip (`width - p[0]`) on all landmark coordinates without
   swapping left/right landmark indices. When the user points their arms backward
   (behind the body), the X-flip reverses the arm's angular direction relative to
   the body center — an arm that points "backward" in real life is drawn pointing
   "forward" on the mirrored character. A correct mirror must swap left/right
   landmark indices *and* X-flip, so that limb directions are preserved relative to
   the body midline (just like a real mirror, where your right arm movement maps to
   the mirror-figure's left arm with the same pose direction).

2. **Face cropping can be more efficient**: The Mario Face game uses
   `mediapipe.solutions.face_mesh.FaceMesh` (solution API, bundled model) for face
   landmark detection. The user now provides a dedicated
   `models/face_landmarker.task` file (MediaPipe Tasks API FaceLandmarker,
   `float32/latest`). Switching to the Tasks API model — already the framework used
   by the existing PoseLandmarker pipeline — and leveraging its face bounding box
   output will produce tighter, more efficient face crops than the current
   contour-landmark heuristic in `FaceCropper.crop_face()`.

## What Changes

- **Modify `src/character.py`** — Replace the pure X-flip `mirror_points()` with a
  mirror that swaps left/right landmark index pairs (shoulders, elbows, wrists,
  hips, knees, ankles, etc.) before applying the X-flip, preserving limb direction
  relative to the body centerline.
- **Add `src/face_landmarker.py`** — New `FaceLandmarkerDetector` class wrapping
  `mediapipe.tasks.vision.FaceLandmarker` with the `models/face_landmarker.task`
  model file, replacing the FaceMesh solution API wrapper.
- **Modify `src/face_crop.py`** — Update `FaceCropper.crop_face()` to accept a face
  bounding box (when available from the Tasks API result) for tighter, more
  efficient cropping; fall back to the existing contour-landmark heuristic when the
  bounding box is unavailable.
- **Modify `src/mario_face_game.py`** — Wire the new `FaceLandmarkerDetector` into
  the pipeline alongside the existing PoseLandmarker.
- **Add tests** for the corrected mirror swap logic and the new face landmarker
  detector / bounding-box crop path.

## Capabilities

### New Capabilities

- `face-landmarker-task`: A MediaPipe Tasks API FaceLandmarker (`face_landmarker.task`)
  that detects 468 face landmarks and a face bounding box per detected face, running
  in the same Tasks API pipeline as the existing PoseLandmarker.

### Modified Capabilities

- `camera-pose-silhouette`: The mirror-mode requirement is updated so that limb
  directions are preserved relative to the body centerline (left/right landmarks are
  swapped) rather than blindly X-flipped, fixing arm direction when limbs point
  backward.
- `mario-face-capture`: Face detection switches from the bundled FaceMesh solution
  API to the `face_landmarker.task` Tasks API model, and face cropping uses the
  face bounding box for tighter, more efficient crops.

## Impact

- **New**: `src/face_landmarker.py` — FaceLandmarker Tasks API wrapper.
- **Modified**: `src/character.py` — `mirror_points()` rewritten to swap
  left/right landmark pairs; updated `MimicCharacter` and `CharacterManager` as
  needed.
- **Modified**: `src/face_crop.py` — `crop_face()` accepts an optional
  bounding-box parameter for tighter crop computation.
- **Modified**: `src/mario_face_game.py` — uses `FaceLandmarkerDetector` instead of
  `FaceDetector`.
- **Modified**: `src/main.py`, `run.sh` — download `face_landmarker.task` at first
  run alongside the pose model.
- **Modified**: `tests/test_character.py` — updated mirror tests, new swap-logic
  tests.
- **Modified**: `tests/test_mario_face_game.py` — updated face detector tests to use
  the new Task-based detector, new bounding-box crop tests.
- **Optional**: `src/face_detector.py` — may be left in place for backward
  compatibility or removed if the Tasks API fully supersedes it.
