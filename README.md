# Juego Camara

A real-time 2D game framework controlled by body movements in front of a webcam.
MediaPipe PoseLandmarker tracks the player's body landmarks (shoulders, arms,
legs); physically jumping in front of the camera makes the game character jump
over an endless stream of obstacles.

The repository ships one playable game — **Mario Face** — and is organized so
that new 2D games can be added reusing the same camera, pose-detection, audio,
and jump-game building blocks.

## Requirements

- Python 3.10+
- Linux Ubuntu with a webcam (`/dev/video0`)
- Python packages: mediapipe, opencv-python, numpy, pygame

## Installation

```bash
pip install -r requirements.txt
```

The game downloads two MediaPipe model files automatically on first run (cached
in `models/`, not committed to git). To download them manually:

```bash
mkdir -p models
wget -O models/pose_landmarker_heavy.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float32/latest/pose_landmarker_heavy.task
wget -O models/face_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
```

## Usage

```bash
./run_mario_face.sh
```

Or:

```bash
python3 -m src.games.mario
```

### Camera Selection

To use a specific webcam (useful when multiple cameras are connected), pass
the `--camera` / `-c` flag with the device index:

```bash
./run_mario_face.sh --camera 2          # Uses /dev/video2
python3 -m src.games.mario -c 2         # Same, via Python
```

Find available cameras with:

```bash
ls /dev/video*
```

## Mario Face Game

A Mario Bros-themed variant where the player's **real face** (captured from the
webcam) replaces the Mario character's head entirely. The character's body
mimics the player's pose and jump via PoseLandmarker body landmarks (red shirt
for arms/torso, blue overalls for legs), but the head is a real face crop
instead of a peach face circle + cap + hair arc. When the face landmarker fails
to detect a face, the character falls back to the standard Mario head.

### Controls

- Physically **jump** to make Mario jump and clear obstacles
- **Double jump**: Jump a second time while airborne to reach a higher apex
  (maximum 2 jumps per airtime)
- `SPACE` — Start game (from menu) / restart (after game over)
- `q` or `ESC` — Quit

### Features

- **Lives system**: The player has 3 lives (hearts). Each collision with an
  obstacle costs a life; sky blocks restore lives when collected. The game ends
  when all lives are lost.
- **Level progression**: Every 5 obstacles cleared the player levels up; speed
  increases ×1.10 per level from level 2, and obstacle spawn gaps tighten.
- **Obstacle types**: Pipes, "?" blocks, and goombas, each with its own size
  and appearance.
- **Background music**: A ground theme plays during gameplay and an
  invincibility theme at high scores; sound effects cover coin pickups and game
  over. Runs silently without errors on headless machines.
- **Pose stability**: If the player is too close to or too far from the camera,
  a warning is shown and the game pauses until the pose returns to an acceptable
  range.
- **Sprite background**: Sky blocks and clouds are rendered from sprites in
  `sprites/`.

### How it works

1. **Camera capture** — OpenCV reads frames from the webcam via V4L2
2. **Pose detection** — MediaPipe PoseLandmarker detects 33 body landmarks
3. **Face detection** — MediaPipe FaceLandmarker detects 468 face landmarks per
   frame using `models/face_landmarker.task`
4. **Face cropping** — The face region is cropped from the BGR camera frame
   using face contour landmarks, producing a circular face image with alpha mask
5. **Character rendering** — The face crop is overlaid at the character's nose
   landmark position, replacing the Mario head circle

## Architecture

The codebase is split into three layers so new 2D games can be added by
reusing shared infrastructure:

```
src/
├── core/                    # Shared, game-agnostic infrastructure
│   ├── camera.py            #   Webcam capture (V4L2) and frame preprocessing
│   ├── pose_detector.py     #   PoseLandmarker wrapper → PoseResult landmarks
│   ├── face_landmarker.py   #   FaceLandmarker wrapper (468 face landmarks)
│   ├── face_crop.py         #   Circular face crop + alpha mask from landmarks
│   ├── silhouette.py        #   Silhouette/sprite drawing helpers & palettes
│   ├── sound_manager.py     #   Music/SFX via pygame.mixer (degrades gracefully)
│   ├── utils.py             #   LandmarkPoint, rgb_to_mp_image, etc.
│   └── character.py         #   mirror_points landmark mirroring
├── framework/
│   └── jump_game.py         # Reusable 2D platformer framework: JumpDetector,
│                            #   PlayerCharacter, Obstacle/ObstacleManager,
│                            #   SkyBlock, Cloud, GameEngine loop & constants
└── games/
    └── mario/               # One game per directory
        ├── mario_game.py        # Mario-themed jump game (parent variant)
        ├── mario_face_game.py   # Mario Face variant (real-face head)
        ├── main.py              # CLI entry point (also exposes main())
        └── __main__.py          # Enables `python3 -m src.games.mario`
```

### Adding a new 2D game

1. Create `src/games/<name>/` with an `__init__.py`, a game module that either
   subclasses the framework's `GameEngine` (from
   `src.framework.jump_game`) or reuses its building blocks, a `main.py` entry
   point, and a `__main__.py` (`from .main import main; ...`).
2. Use `from ...core import ...` / `from ...framework.jump_game import ...`
   (three-dot relative imports) to reach shared infrastructure.
3. Add a `run_<name>.sh` launcher that `cd`s into the repo root and runs
   `python3 -m src.games.<name>`.
4. Place tests under `tests/games/<name>/` (or `tests/core/` /
   `tests/framework/` for shared code) and update this README.

## Tests

```bash
python3 -m pytest -q
```

Unit tests cover the core helpers, the jump-game framework, and each game
engine; they run without a camera or model files using mock landmark data.

## Controls

- `q` — Quit the application
- `m` — Toggle mirror mode (characters move symmetrically with the users)
- `s` — Cycle rendering style:
  - **Style 0**: Full silhouette (mask + colored body parts + skeleton + joints)
  - **Style 1**: Body polygons + skeleton + joints (no mask fill)
  - **Style 2**: Skeleton + joints only (on camera feed)
  - **Style 3**: Stick figure (dimmed background + skeleton + joints)
  - **Style 4**: Pure stick figure (black background, no camera feed visible)
  - **Style 5**: Head circle + body lines (circle for head, lines for body, solid black background)

### Multi-person mode

The application detects up to 4 people simultaneously. Each person is rendered
as a character with a distinct color:

| Color | Person |
|-------|--------|
| White | Person 0 |
| Red   | Person 1 |
| Green | Person 2 |
| Blue  | Person 3 |