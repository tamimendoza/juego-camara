## 1. Infrastructure

- [x] 1.1 Add `models/` to `.gitignore`
- [x] 1.2 Update `run.sh` to download `pose_landmarker_lite.task` if missing
- [x] 1.3 Add model download note to `requirements.txt`

## 2. Utility Functions

- [x] 2.1 Update `landmarks_to_pixels()` to handle `presence` field from PoseLandmarker
- [x] 2.2 Add `rgb_to_mp_image()` helper in `utils.py`
- [x] 2.3 Add `mp_image_to_numpy()` helper in `utils.py`
- [x] 2.4 Add unit tests for updated/new utilities

## 3. Pose Detector Migration

- [x] 3.1 Replace `mp.solutions.pose.Pose` with `mp.tasks.vision.PoseLandmarker` in `src/pose_detector.py`
- [x] 3.2 Update `detect()` to accept `mp.Image`, return `List[PoseResult]`
- [x] 3.3 Convert segmentation masks from `mp.Image` to numpy arrays
- [x] 3.4 Add `num_poses` parameter (default 4)
- [x] 3.5 Add unit tests for multi-pose detection

## 4. Character Manager

- [x] 4.1 Add `CharacterManager` class to `src/character.py`
- [x] 4.2 Add per-character color palette
- [x] 4.3 Modify `MimicCharacter` to accept color offset
- [x] 4.4 Implement character lifecycle (create/update/remove by index)
- [x] 4.5 Add lifecycle tests in `tests/test_character.py`

## 5. Main Pipeline

- [x] 5.1 Update `main.py` to convert BGR → RGB → mp.Image before detection
- [x] 5.2 Replace `MimicCharacter` with `CharacterManager` in the pipeline
- [x] 5.3 Update keyboard controls to delegate to `CharacterManager`

## 6. Documentation & Verification

- [x] 6.1 Update `README.md` with multi-person mode documentation
- [x] 6.2 Run `pytest tests/` — all tests pass
