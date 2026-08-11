## 1. Mirror mode arm-direction fix

- [x] 1.1 Add `_MIRROR_LANDMARK_MAP` dict to `src/character.py` mapping each left/right landmark pair (e.g., 11↔12, 13↔14, 15↔16, 17↔18, 19↔20, 21↔22, 23↔24, 25↔26, 27↔28, 29↔30, 31↔32)
- [x] 1.2 Rewrite `mirror_points()` to swap left/right indices first, then X-flip coordinates; preserve `None` handling and head landmarks (0–10) as X-flip-only
- [x] 1.3 Update existing mirror tests in `tests/test_character.py` for the new swap-then-flip semantics
- [x] 1.4 Add new tests verifying arm direction is preserved when pointing backward (e.g., right arm extended laterally stays lateral after mirror, not reversed to medial)

## 2. FaceLandmarker Tasks API detector

- [x] 2.1 Create `src/face_landmarker.py` — `FaceLandmarkerDetector` class wrapping `mediapipe.tasks.vision.FaceLandmarker` with `models/face_landmarker.task` in VIDEO running mode
- [x] 2.2 Implement `detect(rgb_frame, timestamp_ms) -> tuple[face_landmarks, face_bbox]` returning 468 landmarks and bounding box (or None)
- [x] 2.3 Implement graceful fallback: if `face_landmarker.task` is missing, raise `FileNotFoundError` with a clear message (same pattern as `PoseDetector`)
- [x] 2.4 Add unit tests in `tests/test_mario_face_game.py` for `FaceLandmarkerDetector` (mock the Tasks API, verify landmark + bbox passthrough, no-face returns None)

## 3. FaceCropper bounding-box support

- [x] 3.1 Extend `FaceCropper.crop_face()` in `src/face_crop.py` with optional `face_bbox` parameter (tuple of x, y, width, height in pixels)
- [x] 3.2 When `face_bbox` is provided, compute crop center and radius from the bounding box for a tighter, more efficient crop; when absent, use the existing contour-landmark heuristic unchanged
- [x] 3.3 Add tests for the bounding-box crop path and the fallback path in `tests/test_mario_face_game.py`

## 4. Wire FaceLandmarker into Mario Face game

- [x] 4.1 Modify `MarioFaceGameEngine.__init__` to accept a `face_landmarker: FaceLandmarkerDetector` and update `MarioFaceGameEngine.detect_face` to call the new detector and pass the bounding box to `crop_face()`
- [x] 4.2 Update `src/mario_face_main.py` to instantiate `FaceLandmarkerDetector` instead of `FaceDetector`
- [x] 4.3 Update `run_mario_face.sh` to download `models/face_landmarker.task` on first run (alongside the pose model)

## 5. Verification

- [x] 5.1 Run `pytest tests/test_character.py -v` — all pass (including new mirror swap tests)
- [x] 5.2 Run `pytest tests/test_mario_face_game.py -v` — all pass (including FaceLandmarker + bbox crop tests)
- [x] 5.3 Run `pytest tests/ -v` — full suite passes, no regressions
- [x] 5.4 Run `openspec validate --change "mirror-arm-direction-and-face-landmarker-crop"`
