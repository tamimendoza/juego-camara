## 1. Leg-driven two-phase jump detection

- [ ] 1.1 Add crouch/jump constants to `src/game.py`: `CROUCH_ANGLE_THRESHOLD` (150.0), `CROUCH_HOLD_FRAMES` (4), `ARMED_TIMEOUT_FRAMES` (20), `ANKLE_RISE_THRESHOLD` (10.0); keep `JUMP_THRESHOLD` (30.0) and `JUMP_COOLDOWN` (8).
- [ ] 1.2 Add a `_knee_angle(points, hip, knee, ankle)` helper in `JumpDetector` that returns the angle in degrees (arccos of the normalized vectors), guarding against None landmarks and zero-length vectors.
- [ ] 1.3 Add `_is_crouched(landmarks)` in `JumpDetector` returning True only when both knees (25/26) and ankles (27/28) are visible and the average knee angle is below `CROUCH_ANGLE_THRESHOLD`.
- [ ] 1.4 Add an `_ankle_midpoint_y(landmarks)` helper (landmarks 27/28) and reuse `_shoulder_midpoint_y` for the fire condition.
- [ ] 1.5 Implement the two-phase state machine in `JumpDetector.update()`: in `IDLE`, keep the EMA shoulder baseline and arm when `_is_crouched` holds for `CROUCH_HOLD_FRAMES` consecutive frames; in `ARMED`, fire when the shoulder midpoint AND the ankle midpoint both rise above their crouch baselines by `JUMP_THRESHOLD` / `ANKLE_RISE_THRESHOLD`, then enter the existing cooldown; expire the arm state after `ARMED_TIMEOUT_FRAMES`.
- [ ] 1.6 Ensure `reset()` clears the new `ARMED` state and crouch counters alongside the baseline and cooldown.
- [ ] 1.7 Confirm no engine changes are needed: `game.py`, `mario_game.py`, `mario_face_game.py`, `minecraft_game.py` keep calling `jump_detector.update(landmarks)` and `player.jump()` (the detector stays airborne-agnostic).

## 2. Solid torso fill

- [ ] 2.1 Add a `"torso_fill"` style to `SilhouetteDrawer.render_character` in `src/silhouette.py` that fills the torso quadrilateral (`get_visible_polygon(points, [11, 12, 24, 23])`) with `self.silhouette_color` via `cv2.fillPoly`, drawn before skeleton/body-line layers.
- [ ] 2.2 Enable `"torso_fill"` in `PlayerCharacter.render` (`src/game.py`): styles become `["torso_fill", "head_circle", "body_lines"]`.
- [ ] 2.3 Enable `"torso_fill"` in `MarioCharacter.render` (`src/mario_game.py`): styles become `["torso_fill", "mario_head", "mario_body"]`.
- [ ] 2.4 Enable `"torso_fill"` in `MarioFaceCharacter.render` (`src/mario_face_game.py`) for both the face and fallback style lists (`["torso_fill", "mario_body", "face_overlay"]` and `["torso_fill", "mario_head", "mario_body"]`).
- [ ] 2.5 Leave `minecraft_game.py` rendering unchanged (torso already a filled voxel block).

## 3. Clamp jumps to the visible area

- [ ] 3.1 Add `TOP_MARGIN` (10) and a `MAX_JUMP_OFFSET = ground_y - TOP_MARGIN - CHARACTER_TARGET_HEIGHT` computation to `PlayerCharacter` in `src/game.py`; clamp `_jump_offset` in `update()` and zero `_vy` when the clamp engages.
- [ ] 3.2 Apply the same clamp in `MarioCharacter` (`src/mario_game.py`) and `MinecraftMarioCharacter` (`src/minecraft_game.py`), each using its own `CHARACTER_TARGET_HEIGHT`.
- [ ] 3.3 Confirm `MarioFaceCharacter` inherits the clamp from `MarioCharacter` without further changes.

## 4. Fixed-size game windows (no zoom)

- [ ] 4.1 Change `cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)` to `cv2.WINDOW_AUTOSIZE` in `src/game_main.py`.
- [ ] 4.2 Do the same in `src/mario_main.py`, `src/minecraft_main.py`, and `src/mario_face_main.py`.

## 5. Tests

- [ ] 5.1 Add a crouch landmark helper (bent knees) to `tests/test_game.py` alongside the existing `make_landmarks`/`make_standing_landmarks` helpers.
- [ ] 5.2 Update `TestJumpDetector` in `tests/test_game.py`: standing still → no jump; crouch alone → no jump; crouch then jump (shoulders + ankles rise) → jump fires; shoulders-only rise → no jump; crouch then stand up (ankles stay) → no jump; missing knees/ankles → no jump; cooldown still blocks; `reset()` clears the armed state.
- [ ] 5.3 Update engine-level jump tests (`test_jump_detected_during_play`, `test_double_jump_detected_during_play`) in `tests/test_game.py` to feed crouch-then-jump landmark sequences.
- [ ] 5.4 Add a test that the character's apex (including a double jump) never puts the bounding box above `TOP_MARGIN` (clamp engaged) in `tests/test_game.py`.
- [ ] 5.5 Add a render test asserting the torso region is filled with `silhouette_color` for the `torso_fill` style (in `tests/test_silhouette.py` or `tests/test_game.py`).
- [ ] 5.6 Update the corresponding jump/clamp expectations in `tests/test_mario_game.py`, `tests/test_mario_face_game.py`, and `tests/test_minecraft_game.py` for the new two-phase gesture and the on-screen clamp.
- [ ] 5.7 Run `pytest` and ensure the full suite passes.

## 6. Docs

- [ ] 6.1 Update `README.md` controls/mechanics: jumping now requires bending the legs and then jumping; note the fixed-size window and that the character stays on screen.
