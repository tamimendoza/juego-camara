## Why

We need a real-time camera application that detects a person's pose and draws a silhouette character that mimics their movements on Linux Ubuntu. This enables interactive camera-based games and AR experiences where a stylized on-screen character mirrors the user's body position in real time.

## What Changes

- Add a Python application that captures webcam video via OpenCV with the V4L2 backend
- Integrate MediaPipe Pose for real-time 33-landmark body detection (head, arms, torso, legs)
- Enable MediaPipe segmentation to extract a precise body silhouette mask
- Draw a colored silhouette overlay on the live camera feed using the segmentation mask
- Render a landmark-based skeleton character that mimics the user's pose in real time
- Add landmark visibility filtering so occluded body parts are not drawn
- Add smoothing for jitter-free landmark tracking
- Provide hotkeys: `q` (quit), `m` (toggle mirror), `s` (toggle style)

## Capabilities

### New Capabilities

- `camera-pose-silhouette`: Real-time webcam pose detection with silhouette and mimicking character rendering on Linux Ubuntu

### Modified Capabilities

*(none — this is a new capability)*

## Impact

- New Python source files under `src/` (camera.py, pose_detector.py, silhouette.py, character.py, utils.py, main.py)
- New `requirements.txt` with pinned versions of mediapipe, opencv-python, numpy, pygame
- New `run.sh` launch script
- New `tests/` directory with unit tests for coordinate transforms and body part mapping
- No existing code, APIs, or systems are modified
