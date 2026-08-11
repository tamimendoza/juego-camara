## Context

The silhouette application (`src/main.py` + `src/character.py`) provides a `m`
key to toggle mirror mode. The current `mirror_points()` function performs a pure
X-axis flip (`width - p[0]`) on every landmark coordinate **without** swapping
left and right landmark indices. Because the skeleton/character rendering uses
fixed index groups (`BODY_PART_GROUPS` in `src/utils.py`), the X-flip reverses
the angular direction of every limb relative to the body centerline. When the
user extends an arm backward (wrist on the body's-side / medial side), the flip
makes it appear to point forward (lateral side) on the mirrored character.

The Mario Face game (`src/mario_face_game.py`) currently uses
`mediapipe.solutions.face_mesh.FaceMesh` (solution API, bundled model) for face
landmark detection and `src/face_crop.py` (`FaceCropper`) to extract a circular
face crop. The user now provides `models/face_landmarker.task` — a MediaPipe
Tasks API FaceLandmarker model — which is the same API framework already used by
the existing `PoseDetector` (`mediapipe.tasks.vision.PoseLandmarker`).

**MediaPipe version**: 0.10.3 (per `requirements.txt`). The Tasks API
`FaceLandmarker` is available, but `face_bounding_boxes` in the result object was
introduced in a later release — this must be verified at implement time. See Open
Questions.

## Goals / Non-Goals

**Goals:**
- Fix mirror mode so that limb directions are preserved relative to the body
  centerline when the user extends arms backward or to the side.
- Switch face detection in the Mario Face game from the FaceMesh solution API to
  the FaceLandmarker Tasks API (`models/face_landmarker.task`).
- Use the face bounding box from FaceLandmarker (when available) for tighter,
  more efficient face crops; fall back to the contour-landmark heuristic when the
  bounding box is absent.

**Non-Goals:**
- No changes to game mechanics (jump physics, obstacle spawning, levels, lives,
  sounds, backgrounds) in any game variant.
- No changes to non-mirror rendering in the silhouette app (`src/main.py`
  `CharacterManager` outside of mirror mode).
- No changes to the Minecraft or base Mario game variants.
- The `src/face_detector.py` file (FaceMesh wrapper) is left in place during this
  change as a fallback; removing it is deferred to avoid breaking the
  `mario-face-capture` tests if the Tasks API model is unavailable.

## Decisions

### Decision 1: Swap left/right landmark indices, then X-flip

**Choice:** Rewrite `mirror_points()` to first swap each symmetric left/right
landmark pair (11↔12, 13↔14, 15↔16, 17↔18, 19↔20, 21↔22, 23↔24, 25↔26, 27↔28,
29↔30, 31↔32), then apply `width - x` to the X coordinate of every point.

**Rationale:** In a real mirror, your right arm maps to the mirror-figure's left
arm *at the mirrored position* — the limb shape/direction relative to the body
center is preserved. A pure X-flip moves the points but keeps the same index
labels, so the rendered limb (e.g., "right arm" polygon) gets drawn on the left
side with a reversed angular direction. Swapping indices first means the
character's left-arm polygon is drawn from the user's right-arm landmarks at the
mirrored X position — matching real-mirror behavior where arm direction is
preserved relative to the body midline.

**Alternatives considered:**
- *Pure X-flip only* (current): simple but reverses limb directions — the bug.
- *Index swap only, no X-flip*: produces a "same-side" reflection, not a true
  mirror. Rejected.

Head/face landmarks (indices 0–10) are NOT swapped because they are mostly
midline or asymmetric (nose at center, eyes/ears paired). They are only
X-flipped. This is consistent with the user's taste: no facial feature
rendering, so head landmarks are only used for the nose-centered head circle /
body-lines rendering where symmetry is not critical.

### Decision 2: New `FaceLandmarkerDetector` class using Tasks API

**Choice:** Create `src/face_landmarker.py` with a `FaceLandmarkerDetector`
class wrapping `mediapipe.tasks.vision.FaceLandmarker` and the
`models/face_landmarker.task` model file. Use it as a drop-in replacement for
`FaceDetector` in `mario_face_game.py`.

**Rationale:** The Tasks API FaceLandmarker is the same framework as the existing
`PoseDetector` (both use `mediapipe.tasks.vision` with `.task` model files and
VIDEO running mode). This creates a single, consistent pipeline. The
`face_landmarker.task` model file is provided by the user. Using a single
`FaceLandmarker` instance alongside the existing `PoseLandmarker` keeps the
video-mode timestamp sequencing consistent.

**Alternatives considered:**
- *Keep FaceMesh solution API*: would not leverage the user's model file or the
  bounding-box output. Rejected.
- *Replace FaceDetector entirely*: would break the `mario-face-capture` tests
  and remove the fallback path if the `.task` file is unavailable. Deferred —
  `face_detector.py` stays as fallback.

### Decision 3: FaceCropper accepts optional bounding box

**Choice:** Extend `FaceCropper.crop_face()` with an optional `face_bbox`
parameter. When provided (from FaceLandmarker), compute the crop center and
radius from the bounding box for a tighter, more efficient crop. When absent
(FaceMesh fallback or legacy model), use the existing contour-landmark
heuristic unchanged.

**Rationale:** The bounding box gives a direct face region (x, y, width, height)
that can be used to center the crop and determine face size without iterating
over 200 contour landmarks. This is the "more efficient face cropping" the user
described. The optional parameter keeps backward compatibility with existing
callers and tests.

## Risks / Trade-offs

- **[Risk] Face bounding box may not be available in MediaPipe 0.10.3.**
  The `FaceLandmarkerResult.face_bounding_boxes` field was introduced in a later
  release. If absent, the crop falls back to contour landmarks — still correct,
  just not more efficient than today.
  → Mitigation: Check for the attribute at runtime with `getattr`; document in
  spec that fallback behavior is acceptable.

- **[Risk] Two Task-based detectors may impact performance.**
  Running both PoseLandmarker and FaceLandmarker Tasks on every frame doubles
  inference cost.
  → Mitigation: Use `min_tracking_confidence=0.5` and `min_face_presence_confidence`
  thresholds. If frame rate drops, FaceLandmarker can run every N frames while
  PoseLandmarker runs every frame (documented as open question).

- **[Risk] Landmark index swap must handle partial detections.**
  MediaPipe PoseLandmarker may return fewer than 33 landmarks if a body part is
  occluded. The swap must gracefully handle `None` points.
  → Mitigation: `mirror_points()` already handles `None` per-point; the swap
  mapping only accesses known indices and falls back to the original position
  for out-of-range indices.

- **[Risk] Left/right landmark pairs differ between PoseLandmarker and the
  legacy `mp.solutions.pose` API.**
  The taste profile uses the newer PoseLandmarker Tasks API (33 landmarks, same
  MediaPipe convention). The standard 33-landmark indices are: 11/12 shoulders,
  13/14 elbows, 15/16 wrists, 17/18 pinkies, 19/20 index, 21/22 thumbs,
  23/24 hips, 25/26 knees, 27/28 ankles, 29/30 heels, 31/32 foot indices.
  → Mitigation: These indices are standard and verified against the MediaPipe
  BlazePose spec used in `utils.py` `BODY_PART_GROUPS`.

## Migration Plan

1. Create `src/face_landmarker.py` — `FaceLandmarkerDetector` wrapping Tasks API
   `FaceLandmarker` with `models/face_landmarker.task`.
2. Rewrite `mirror_points()` in `src/character.py` to swap left/right pairs
   before X-flipping; add a `_MIRROR_LANDMARK_MAP` constant.
3. Extend `FaceCropper.crop_face()` in `src/face_crop.py` with optional
   `face_bbox` parameter.
4. Wire `FaceLandmarkerDetector` into `src/mario_face_game.py`
   (`MarioFaceGameEngine`), passing the bounding box to `crop_face()`.
5. Update `run.sh` (or add a new `run_mario_face.sh` step) to download
   `face_landmarker.task` on first run.
6. Add tests: mirror swap logic in `tests/test_character.py`, FaceLandmarker
   detector + bounding-box crop in `tests/test_mario_face_game.py`.
7. Run `pytest tests/ -v` — full suite must pass.
8. Run `openspec validate --change <name>`.

Rollback: Delete `src/face_landmarker.py`, revert `mirror_points()` to the
original X-flip, revert `FaceCropper.crop_face()` signature, and revert
`mario_face_game.py` to use `FaceDetector`.

## Open Questions

- **Is `face_bounding_boxes` available in the FaceLandmarker result with the
  user's `face_landmarker.task` model and MediaPipe 0.10.3?** If not, the
  bounding-box crop path is skipped and the contour-landmark fallback is used.
  This is a verification step during implementation, not a design blocker — the
  spec explicitly covers the fallback scenario.
