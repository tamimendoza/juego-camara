## Context

The existing `PoseDetector` wraps `mp.solutions.pose.Pose` which detects a single pose (33 landmarks) per frame. `main.py` creates one `MimicCharacter`, calls `character.update(result)`, and renders onto the BGR frame. For multi-person support, we migrate to `mp.tasks.vision.PoseLandmarker` which supports `num_poses > 1` and returns a list of poses. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Detect up to 4 people simultaneously in a single inference pass
- Render each person as a distinct-colored stick-figure character
- Maintain 15–30 FPS at 640×480 on CPU
- Keep all 6 existing rendering styles (including Style 5 head-circle)

**Non-Goals:**
- Person re-identification across frames (index-based matching only)
- Per-person mirror mode toggle (mirror applies globally)
- Configurable `num_poses` at runtime (hardcoded default, configurable via constructor)

## Decisions

### Decision 1: PoseLandmarker with LIVE_STREAM running mode

**Choice:** Use `PoseLandmarker` with `running_mode=LIVE_STREAM` and a `result_callback`, or `running_mode=VIDEO` with explicit timestamps.

**Rationale:** LIVE_STREAM mode is designed for real-time camera input and handles frame dropping internally. However, the current `mp.solutions.pose.Pose` API processes synchronously (returns results directly). To minimize disruption to the main loop, use `running_mode=VIDEO` with explicit timestamps — this provides synchronous `detect_for_video()` calls that block until results are ready, matching the current synchronous pipeline.

**Alternative:** LIVE_STREAM mode with async callback — more complex, requires restructuring the main loop to handle async results.

### Decision 2: Index-based person matching (no re-identification)

**Choice:** Match detected poses to characters by index: pose[0] → character[0], pose[1] → character[1], etc. Create new characters when more poses appear; destroy characters when fewer poses are detected.

**Rationale:** Full person re-identification (tracking) adds significant complexity (IoU matching, Kalman filters, etc.) for marginal benefit in a 2–4 person home setting. Simple index-based matching is robust enough: MediaPipe's multi-person detector is fairly stable frame-to-frame, and characters are re-created each time a new person appears.

### Decision 3: Color palette for distinct characters

**Choice:** Define a fixed palette of 4 distinct colors in `CharacterManager`. Each character's `SilhouetteDrawer` gets a color offset that shifts `line_color` and `joint_color`.

**Palette:** White (default), Red, Green, Blue (in BGR: `(255,255,255)`, `(0,0,255)`, `(0,255,0)`, `(255,0,0)`)

**Rationale:** Simple and effective. Users can distinguish people by color. Extending the palette is trivial.

### Decision 4: Model file download in run.sh

**Choice:** `run.sh` checks for `models/pose_landmarker_lite.task` and downloads via `wget` if missing. Falls back to `curl` if `wget` is unavailable.

**Rationale:** Avoids committing a binary to git. The download is a single command. Error handling ensures the user gets a clear message if there's no internet.

### Decision 5: PoseResult remains a single-pose dataclass

**Choice:** Keep `PoseResult` as-is (single pose). `PoseDetector.detect()` returns `List[PoseResult]` instead of a single `PoseResult`. Empty list = no person detected.

**Rationale:** `MimicCharacter.update()` already accepts a `PoseResult` — no changes to that interface. `CharacterManager` iterates the list and dispatches each to a character.

### Decision 6: BGR → RGB → mp.Image conversion in main.py

**Choice:** In `main.py`, convert the BGR frame to RGB (already done), then wrap in `mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_array)` before calling `detect()`.

**Rationale:** `PoseLandmarker.detect_for_video()` requires an `mp.Image` object, not a numpy array. The conversion is a lightweight wrapper with no data copy (uses numpy view).

## Risks / Trade-offs

- **[Risk] Model file download may fail (no internet).** → Mitigation: check for file at startup, fall back to `mp.solutions.pose.Pose` single-person mode if model is missing, print clear error message.
- **[Risk] Multi-person detection is slower than single-person.** → Mitigation: use the Lite model and `model_complexity=1` equivalent. Expect 15-30 FPS at 640×480 with 4 people.
- **[Risk] Index-based matching causes color flickering when people swap positions.** → Mitigation: this is a known limitation; full re-identification is out of scope for MVP. Users who need stable IDs should request the tracking feature separately.
- **[Risk] `mp.Image` conversion adds overhead.** → Mitigation: the conversion is a zero-copy view, negligible overhead.

## Open Questions

*(none — all decisions resolved)*
