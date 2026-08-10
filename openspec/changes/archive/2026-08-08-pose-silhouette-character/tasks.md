## 1. Project Setup

- [x] 1.1 Create requirements.txt with pinned versions (mediapipe==0.10.3, opencv-python==4.8.0.76, numpy==1.26.4, pygame==2.5.1)
- [x] 1.2 Create run.sh launch script (python3 src/main.py)
- [x] 1.3 Create .gitignore (exclude __pycache__, .pyc, venv/)
- [x] 1.4 Create src/__init__.py and tests/__init__.py

## 2. Core Modules

- [x] 2.1 Implement src/camera.py — Camera class wrapping cv2.VideoCapture(0, cv2.CAP_V4L2), read_frame() returns BGR frame, release(), configurable resolution
- [x] 2.2 Implement src/pose_detector.py — PoseDetector class wrapping mp.solutions.Pose(enable_segmentation=True, model_complexity=1), detect() returns PoseResult with landmarks, segmentation_mask, world_landmarks
- [x] 2.3 Implement src/utils.py — normalized_to_pixel(), landmarks_to_pixels(), smooth_landmarks() (EMA α=0.3), BODY_PART_GROUPS and LIMB_TRIANGLES dicts, get_visible_polygon()

## 3. Silhouette & Character

- [x] 3.1 Implement src/silhouette.py — SilhouetteDrawer: threshold_mask(), fill_silhouette() (findContours + fillConvexPoly), draw_body_polygons() (fillPoly for body parts), draw_skeleton(), draw_joints(), render_character()
- [x] 3.2 Implement src/character.py — MimicCharacter: update() with landmark smoothing, render() draws silhouette + skeleton, toggle_mirror(), cycle_style()
- [x] 3.3 Implement src/main.py — main pipeline loop: camera.read_frame → RGB conversion → pose_detector.detect → character.update → character.render → cv2.imshow → cv2.waitKey, hotkeys (q/m/s)

## 4. Testing & Verification

- [x] 4.1 Write tests/test_utils.py — 18 unit tests for normalized_to_pixel, smooth_landmarks, get_visible_polygon, body part groups
- [x] 4.2 Run pytest tests/ — all 18 tests pass
- [x] 4.3 Verify end-to-end: 10/10 frames with pose detection, no crashes
- [x] 4.4 Sync delta spec to main specs and archive change via openspec-sync-specs and openspec-archive-change
