## Context

The project `juego-camara` is an empty repository scaffold with OpenSpec tooling configured but no application code. Python 3.10 is available on Ubuntu with the following packages pre-installed in the user site-packages:

- `mediapipe` 0.10.3 — provides `mp.solutions.Pose` with 33 landmarks, `POSE_CONNECTIONS`, `enable_segmentation` option, and a `segmentation_mask` output
- `opencv-python` 4.8.0.76 — provides `cv2.VideoCapture` with `CV_CAP_V4L2` (Linux V4L2 backend), `cv2.findContours`, `cv2.fillConvexPoly`, `cv2.fillPoly`, `cv2.imshow`
- `numpy` 1.26.4 — array operations for mask thresholding and coordinate conversion
- `pygame` 2.5.1 — available but not required for MVP

The system targets Linux Ubuntu with a standard USB webcam at `/dev/video0`.

## Goals / Non-Goals

**Goals:**
- Capture camera video in real time using V4L2 on Ubuntu
- Detect 33-body-landmark pose including head, arms, legs, and torso
- Draw a silhouette character on the live camera feed that mimics the user's movements
- Achieve 30+ FPS at 640×480 resolution
- Provide a clean, testable module structure (camera, pose detection, silhouette, character, main)

**Non-Goals:**
- Multiplayer / multi-person tracking (MediaPipe Pose targets the most prominent person)
- AI character animation (no facial expressions, speech, or procedural movement beyond pose mimicry)
- Mobile platforms (Linux/Ubuntu desktop only)
- Pygame-based advanced graphics rendering (OpenCV handles all drawing for MVP)

## Decisions

### Decision 1: MediaPipe Pose for pose estimation

**Choice:** `mp.solutions.Pose` with `enable_segmentation=True`.

**Rationale:** MediaPipe Pose is the best-in-class real-time pose estimator providing exactly 33 landmarks covering head, arms, and legs. It provides both landmark positions (for character skeleton) and a segmentation mask (for silhouette outline), which is rare to find in a single library. It is pre-installed (v0.10.3) and runs on CPU without GPU requirements.

**Alternatives considered:**
- OpenCV + custom heuristic (insufficient accuracy for body part detection)
- MoveNet via TensorFlow (redundant — MediaPipe Pose uses MoveNet internally)
- OpenPose (CMU) (heavier, slower, deprecated Python API)
- YOLO-Pose (good detection but no segmentation mask)

### Decision 2: Two-layer silhouette rendering

**Choice:** Render the silhouette in two layers: (1) segmentation mask for the body outline/fill, and (2) landmark-based polygons for the character skeleton.

**Rationale:** The segmentation mask gives a precise body shape outline that matches the user's actual silhouette. The landmark polygons give articulated body parts (head, arms, legs) that move with the joints — this is what creates the "character that mimics movements" effect. Combining both gives both realism (mask shape) and expressiveness (joint articulation).

**Alternatives considered:**
- Landmark polygons only (no segmentation): would miss the body shape, appearing as just lines/arms/legs
- Segmentation mask only (no landmarks): static body shape, no articulated character

### Decision 3: OpenCV for all rendering

**Choice:** Use `cv2.imshow()` for display and `cv2.fillPoly`, `cv2.fillConvexPoly`, `cv2.drawContours` for drawing.

**Rationale:** OpenCV is already the dependency for camera capture and is lightweight. It provides all needed drawing primitives. Pygame is available but adds unnecessary complexity for the MVP.

**Alternatives considered:**
- Pygame display surface: more capable for sprites/animations but overkill for silhouette drawing
- Matplotlib: not suitable for real-time rendering

### Decision 4: Exponential moving average for landmark smoothing

**Choice:** Apply exponential moving average (EMA) with α=0.3 to landmark pixel coordinates between frames.

**Rationale:** Raw MediaPipe landmarks jitter at ~1-3 pixels between frames. EMA is lightweight (O(1) per landmark) and effective for this level of smoothing. It is simple to implement and test.

**Alternatives considered:**
- Kalman filter: more accurate but complex to tune and initialize
- No smoothing: character jitter is visually distracting

### Decision 5: Body part polygon triangulation

**Choice:** Draw each body part as a filled triangle/polygon using 3-4 landmark vertices:
- Upper arms: shoulder → elbow → wrist (triangle)
- Torso: shoulder-left → shoulder-right → hip-right → hip-left (quadrilateral)
- Legs: hip → knee → ankle → heel (quadrilateral)
- Head: polygon from face landmarks (nose, eyes, ears, mouth)

**Rationale:** Triangles naturally represent limb geometry and scale naturally as the user moves. `cv2.fillPoly` handles both triangles and quadrilaterals. This mirrors how 2D skeletal animation characters are constructed.

## Risks / Trade-offs

- **[Risk] Segmentation mask requires `enable_segmentation=True`, adding 20-30% inference latency.** → **Mitigation:** Set `model_complexity=1` (balanced) rather than 2 (heavy). At 640×480, MediaPipe Pose runs at 40+ FPS even with segmentation.
- **[Risk] Segmentation mask may leak into the background when the person is close to the camera.** → **Mitigation:** Combine with landmark visibility filtering; only draw body part polygons when the corresponding landmarks are visible.
- **[Risk] Landmark jitter causes the character to shake.** → **Mitigation:** EMA smoothing with α=0.3 limits jitter to ±2 pixels.
- **[Risk] Webcam `/dev/video0` may not exist on all Ubuntu systems.** → **Mitigation:** Fall back from `CAP_V4L2` to `CAP_ANY` and report a clear error if no camera is found.
- **[Trade-off] Body part colors are hardcoded in the style dict for simplicity.** → Future: make configurable via a `style` module.

## Open Questions

*(none — all decisions resolved)*
