## 1. OpenSpec artifacts

- [x] 1.1 Create `openspec/changes/mario-face-capture/.openspec.yaml`
- [x] 1.2 Create `proposal.md`
- [x] 1.3 Create `design.md`
- [x] 1.4 Create `specs/mario-face-capture/spec.md`
- [x] 1.5 Create `tasks.md`

## 2. Face detection infrastructure

- [x] 2.1 Create `src/face_detector.py` — `FaceDetector` class wrapping `mediapipe.solutions.face_mesh`
- [x] 2.2 Create `src/face_crop.py` — `FaceCropper` class for extracting circular face region from BGR frame

## 3. SilhouetteDrawer face overlay

- [x] 3.1 Add `draw_face_overlay()` method to `SilhouetteDrawer` in `src/silhouette.py`
- [x] 3.2 Wire `"face_overlay"` into `render_character()` dispatch in `src/silhouette.py`
- [x] 3.3 Add tests in `tests/test_silhouette.py` for face overlay rendering

## 4. Mario face game engine

- [x] 4.1 Create `src/mario_face_game.py` skeleton with imports and constants
- [x] 4.2 Implement `MarioFaceCharacter` (inherits MarioCharacter physics, replaces head with face overlay)
- [x] 4.3 Implement `MarioFaceGameEngine` (extends MarioGameEngine, adds FaceMesh + FaceCropper pipeline)

## 5. Entry point and launch script

- [x] 5.1 Create `src/mario_face_main.py` (mirrors mario_main.py with FaceMesh)
- [x] 5.2 Create `run_mario_face.sh` (mirrors run_mario.sh, forwards "$@")
- [x] 5.3 Make `run_mario_face.sh` executable

## 6. Tests

- [x] 6.1 Create `tests/test_mario_face_game.py` mirroring `test_mario_game.py` patterns
- [x] 6.2 Test MarioFaceCharacter: jump physics, bbox, reset, rendering with face overlay
- [x] 6.3 Test FaceCropper: face crop extraction, circular mask, resize
- [x] 6.4 Test FaceDetector: face landmark detection, fallback when no face
- [x] 6.5 Test MarioFaceGameEngine: states, jump detection, collision, background, HUD

## 7. Documentation

- [x] 7.1 Update `README.md` with "## Mario Face Game" section

## 8. Verification

- [x] 8.1 Run `pytest tests/test_mario_face_game.py -v` — all pass
- [x] 8.2 Run `pytest tests/test_silhouette.py -v` — all pass (including new face overlay tests)
- [x] 8.3 Run `pytest tests/ -v` — full suite passes, no regressions
- [x] 8.4 Run `openspec validate` — change is complete

## 9. Bug fix — NormalizedLandmarkList handling

- [x] 9.1 Fix `FaceCropper.crop_face` in `src/face_crop.py` to unwrap
      `NormalizedLandmarkList.landmark` (the `.landmark` attribute holds the
      iterable list of `NormalizedLandmark` objects; the list object itself is
      not iterable)
- [x] 9.2 Add `make_face_landmark_list` test helper and
      `test_crop_face_accepts_normalized_landmark_list` regression test in
      `tests/test_mario_face_game.py`
- [x] 9.3 Re-run full test suite — all 386 tests pass