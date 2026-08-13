## Why

The current `mp.solutions.pose.Pose` API detects only a single person per frame. Users want to detect and render multiple people simultaneously. Migrating to `mp.tasks.vision.PoseLandmarker` provides native multi-person support via the `num_poses` parameter, running detection for all people in a single inference pass.

## What Changes

- **Replace `PoseDetector`** (wrapping `mp.solutions.pose.Pose`) with a `PoseLandmarker`-based implementation that returns `List[PoseResult]` (one per detected person)
- **Add `CharacterManager`** class in `src/character.py` that manages one `MimicCharacter` per detected person, with a distinct color per character
- **Update `main.py`** to convert the BGR camera frame to RGB → `mp.Image` before detection, and to use `CharacterManager` instead of a single `MimicCharacter`
- **Update `utils.py`** to handle the `presence` field from `PoseLandmarker` results and add `mp.Image` conversion helpers
- **Download model file** (`pose_landmarker_heavy.task`) via `run.sh` at startup; add `models/` to `.gitignore`
- **Add unit tests** for `CharacterManager` lifecycle and updated utilities

## Capabilities

### New Capabilities

- `multi-person-pose-detection`: Real-time detection of multiple people's poses simultaneously, with each person rendered as a colored stick-figure character

### Modified Capabilities

- `camera-pose-silhouette`: The detection backend changes from `mp.solutions.pose.Pose` (single-person) to `mp.tasks.vision.PoseLandmarker` (multi-person). The rendering pipeline now manages multiple characters instead of one.

## Impact

- **New file**: `tests/test_character.py` — tests for `CharacterManager`
- **Modified**: `src/pose_detector.py` — replaced `mp.solutions.pose.Pose` with `mp.tasks.vision.PoseLandmarker`; `detect()` returns `List[PoseResult]`
- **Modified**: `src/utils.py` — `landmarks_to_pixels` handles `presence` field; added `rgb_to_mp_image` and `mp_image_to_numpy` helpers
- **Modified**: `src/character.py` — added `CharacterManager`; `MimicCharacter` accepts per-character color offset
- **Modified**: `src/main.py` — pipeline uses `CharacterManager`, converts frame to `mp.Image`
- **Modified**: `run.sh` — downloads model file if missing
- **Modified**: `.gitignore` — excludes `models/` directory
- **Modified**: `README.md` — documents multi-person mode
- **New dependency**: `pose_landmarker_heavy.task` model file (downloaded at runtime, ~2.5 MB)
