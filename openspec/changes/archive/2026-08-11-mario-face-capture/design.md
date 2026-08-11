## Context

The pose jump game (`src/game.py`) renders a grayscale miniatura stick figure
on a solid black background. The Mario Bros variant (`src/mario_game.py`)
reuses the same pose detection pipeline (`Camera`, `PoseDetector`,
`JumpDetector` from `game.py`) but renders a Mario-styled miniatura character
with a peach face circle, red cap, and brown hair arc, on a sky-blue background
with themed obstacles (pipes, blocks, goombas).

The Mario game currently uses a **separate display canvas** (`np.zeros` solid
sky-blue background) — the camera frame is used **only for pose detection**,
never for rendering. To show the person's real face, the camera frame must be
passed through the rendering pipeline so a face crop can be extracted and
overlaid.

Key existing code referenced:
- `JumpDetector` (game.py): detects jumps from shoulder landmark movement
  (threshold, cooldown, EMA baseline).
- `PlayerCharacter` (game.py): miniatura character with physics (jump velocity
  + gravity), pose scaling to `CHARACTER_TARGET_HEIGHT`.
- `SilhouetteDrawer` (silhouette.py): rendering methods dispatched by style
  strings (`"head_circle"`, `"body_lines"`, `"mario_head"`, `"mario_body"`,
  `"minecraft_head"`, `"minecraft_body"`).
- `MarioCharacter` (mario_game.py): Mario-styled miniatura with jump physics,
  pose scaling, and stability checking.
- `PoseDetector` (pose_detector.py): MediaPipe PoseLandmarker (33 landmarks +
  segmentation mask).
- `SoundManager` (sound_manager.py): pygame.mixer-based audio.

## Goals / Non-Goals

**Goals:**
- Replace Mario's head (peach face circle + red cap + brown hair arc) with the
  person's real face captured from the webcam.
- Show only the face — no cap, no hair arc, no stylized face circle.
- Keep Mario body lines (red shirt for arms/torus, blue overalls for legs).
- Preserve all existing Mario game mechanics: jump physics, double jump,
  obstacle spawning, level progression, speed progression, lives system,
  sky blocks, clouds, graffiti, pose stability warnings, sound effects,
  background music, invincibility theme.
- Create a new separate variant — do not modify existing Mario game or
  silhouette app.
- All new code covered by unit tests, no regressions in existing suite.

**Non-Goals:**
- No changes to the existing Mario game (`mario_game.py`, `mario_main.py`) or
  the base pose jump game (`game.py`, `game_main.py`).
- No changes to the silhouette mirror app (`character.py`, `main.py`).
- No full-head replacement — only the face (no ears, no hair, no cap).
- No pixel-art sprite sheets — rendering uses cv2 primitives + face crop overlay.

## Decisions

### Decision 1: New separate variant, not modifying existing Mario game

**Choice:** Create new files (`mario_face_game.py`, `mario_face_main.py`,
`run_mario_face.sh`) rather than adding face-capture modes to the existing
`mario_game.py`.

**Rationale:** Non-breaking; matches the user's preference for separate
variants; has its own launch script.

### Decision 2: MediaPipe FaceMesh via solution API (not Tasks API)

**Choice:** Use `mediapipe.solutions.face_mesh.FaceMesh` for face landmark
detection, not `mediapipe.tasks.vision.FaceLandmarker`.

**Rationale:** The solution API FaceMesh model is bundled with mediapipe
0.10.3 — no separate model file download is needed (unlike PoseLandmarker
which requires a `.task` file). The Tasks API FaceLandmarker would require
downloading a `face_landmarker.task` model file, adding complexity to the
launch script.

### Decision 3: Face overlay replaces entire Mario head

**Choice:** The `MarioFaceCharacter` renders `["face_overlay", "mario_body"]`
styles. The `draw_face_overlay()` method overlays the real face crop at the
nose position, replacing the peach face circle, red cap, and brown hair arc
entirely.

**Rationale:** The user explicitly answered "Replace entire head with real
face" when asked about cap/no-cap.

### Decision 4: Face crop size matches head circle radius

**Choice:** The face crop is sized to the same radius as the current Mario
head circle: `max(int(shoulder_width * 0.25), 10)` pixels, where shoulder
width is the distance between PoseLandmarker landmarks 11 and 12.

**Rationale:** Maintains the miniatura character proportions. The face is
rendered at the same position and size as the current peach face circle.

**Mario palette (BGR) — body only (head is real face):**
| Element    | Color        | BGR          |
|------------|-------------|-------------|
| Face       | Real face crop | (overlay)  |
| Shirt      | Red         | (0, 60, 255)    |
| Overalls   | Blue        | (180, 0, 0)     |
| Sky        | Blue        | (235, 206, 135) |
| Pipe       | Green       | (0, 180, 0)     |
| Block      | Orange      | (30, 165, 200)  |
| Goomba     | Red-brown   | (0, 50, 200)    |

### Decision 5: Face detection runs in parallel with pose detection

**Choice:** Run FaceMesh on the RGB camera frame in parallel with
PoseLandmarker. Both detectors process the same frame each iteration.

**Rationale:** FaceMesh and PoseLandmarker are independent models — running
them in parallel on the same frame is straightforward. The face landmarks are
used only for face cropping; the pose landmarks drive the character's body
posture and jump detection (unchanged from existing Mario game).

## Risks / Trade-offs

- **[Risk] Face may be too small at miniatura scale (~20px radius).**
  The Mario character is ~90px tall, so the head circle radius is ~15-20px.
  A real face at this size may not be recognizable.
  → Mitigation: Use `refine_landmarks=True` in FaceMesh for maximum detail.
  If testing shows the face is too small, the face crop radius can be
  increased independently of the head circle size (e.g., 1.5x shoulder-based
  radius). This is an open question for the user to confirm during testing.

- **[Risk] FaceMesh may fail if face is small or occluded in camera frame.**
  The person may be too far from the camera for FaceMesh to detect the face.
  → Mitigation: Fall back to the existing Mario head circle when FaceMesh
  fails to detect a face. The character still mimics pose and jump via
  PoseLandmarker.

- **[Risk] Running two MediaPipe models may impact performance.**
  FaceMesh + PoseLandmarker doubles the inference cost per frame.
  → Mitigation: Use `mediapipe.solutions.face_mesh` with
  `min_tracking_confidence=0.5` for efficient tracking. If frame rate drops
  below acceptable, FaceMesh can be run every N frames (e.g., every 3rd frame)
  while PoseLandmarker runs every frame.

- **[Risk] Taste profile conflict — user prefers de-identified rendering.**
  The user's taste profile explicitly states "No facial feature rendering"
  and "de-identified via a circle for the head."
  → Accepted: The user explicitly requested this change, overriding the
  taste profile preference. Documented here for transparency.

## Migration Plan

This is a new, additive feature — no existing code or data is modified in a
breaking way. The only modification to existing files is adding one method
and one style string to `SilhouetteDrawer`, which are opt-in (only activated
when `"face_overlay"` style string is passed).

Deployment steps:
1. Create `src/face_detector.py` and `src/face_crop.py`.
2. Add `draw_face_overlay()` and `"face_overlay"` style to `src/silhouette.py`.
3. Create `src/mario_face_game.py`, `src/mario_face_main.py`, `run_mario_face.sh`.
4. Add tests.
5. Update README.
6. Create OpenSpec artifacts.

Rollback: Delete the new files and revert the one added method + style string
in `src/silhouette.py`.

## Open Questions

- Whether the face crop should be larger than the current head circle radius
  for better recognizability at miniatura scale.
- Whether to run FaceMesh every frame or every N frames for performance.
