# Juego Camara

A real-time camera application that detects multiple people's poses and draws
silhouette characters that mimic their movements on Linux Ubuntu. Up to 4
people are detected simultaneously, each rendered with a distinct color.

## Requirements

- Python 3.10+
- Linux Ubuntu with a webcam (`/dev/video0`)
- Python packages: mediapipe, opencv-python, numpy, pygame

## Installation

```bash
pip install -r requirements.txt
```

The application downloads a MediaPipe pose landmarker model file automatically
when you first run `./run.sh`.  The model is cached in `models/` (not committed
to git — see [.gitignore](.gitignore)).  If you run `python3 -m src.main` directly
instead of `./run.sh`, download the model manually:

```bash
mkdir -p models
wget -O models/pose_landmarker_lite.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float32/latest/pose_landmarker_lite.task
```

## Usage

```bash
./run.sh
```

Or:

```bash
python3 -m src.main
```

### Camera Selection

To use a specific webcam (useful when multiple cameras are connected), pass
the `--camera` / `-c` flag with the device index:

```bash
./run.sh --camera 2        # Uses /dev/video2
python3 -m src.main -c 2   # Same, via Python
```

Find available cameras with:

```bash
ls /dev/video*
```

## Mini Juego (Jump Game)

A mini-game mode where a small character ("miniatura") must jump over an
endless stream of obstacles. The player jumps by **physically jumping** in front
of the webcam — the shoulder landmarks detect the upward movement. Every 10
obstacles cleared, the speed increases by 10%. The game ends on collision.

### Launch

```bash
./run_game.sh
```

Or:

```bash
python3 -m src.game_main
```

The game uses a solid black background (no camera feed) and renders the
character as a head circle + body lines (Style 5), matching the stick-figure
preference. Multiple people can play simultaneously; each person's shoulders
are tracked for jump detection.

### Controls

- Physically **jump** to make the character jump and clear obstacles
- `SPACE` — Start game (from menu) / restart (after game over)
- `q` or `ESC` — Quit

### Game States

| State | Description |
|-------|-------------|
| **Menu** | "Press SPACE to start" — waiting for input |
| **Playing** | Obstacles scroll leftward; jump to avoid them |
| **Game Over** | Final score displayed; press SPACE to restart |

### Level & Speed Progression

Every 10 obstacles cleared, the player levels up. Level 1 (0–9 obstacles) has
base speed; from level 2 onward, speed increases by 10% per level:

```
level = (passed_obstacles // 10) + 1
speed = 4.0 × 1.10^(level - 1)
```

## Mario Bros Game

A Mario Bros-themed variant of the jump game. The camera-detected person is
rendered as a Mario-styled miniatura character (red cap, peach face, red shirt,
blue overalls) that mimics the player's pose and jump. The level features a
sky-blue background with clouds, bushes, and brick ground. Obstacles (pipes,
blocks, goombas) start widely separated so players can advance through levels,
with spacing tightening every 10 obstacles passed. Every 10 obstacles cleared,
the player levels up; from level 2, speed increases 10% per level.

### Launch

```bash
./run_mario.sh
```

Or:

```bash
python3 -m src.mario_main
```

The game uses a themed background (no camera feed) and renders the character as
a small Mario-coloured figure that mirrors the player's pose via scaled
landmark transformation, just like the base jump game.

### Controls

- Physically **jump** to make Mario jump and clear obstacles
- **Double jump**: Jump a second time while airborne to reach a higher apex
  (maximum 2 jumps per airtime)
- `SPACE` — Start game (from menu) / restart (after game over)
- `q` or `ESC` — Quit

### Sound Effects

The Mario game plays audio feedback using `pygame.mixer`:

- **Coin sound** (`mario-moneda.mp3`) — plays when an obstacle is successfully
  cleared by jumping over it
- **Game-over sound** (`mario-bros-game-over-1.mp3`) — plays when the character
  collides with an obstacle

If audio hardware is unavailable (e.g., headless environments), the game runs
silently without errors.

### Level Progression

Every 10 obstacles cleared, the player levels up. Obstacles start very spread
out and tighten with each level:

| Level | Obstacles to reach | Spawn gap range (frames) |
|-------|-------------------|-------------------------|
| 1     | 0                 | 180–280                 |
| 2     | 10                | 150–250                 |
| 3     | 20                | 130–230                 |
| 4     | 30                | 110–200                 |
| 5     | 40                | 90–170                  |
| 6+    | 50+               | 70–130                  |

In addition, game speed increases by ×1.10 from level 2 onward (same as
the base jump game).

### Obstacle Types

| Type   | Appearance             | Size (w×h) |
|--------|------------------------|------------|
| Pipe   | Green rectangle        | 40×80      |
| Block  | Orange brick with "?"  | 40×40      |
| Goomba | Red-brown with eyes    | 30×30      |

## Minecraft Mario Game

A Minecraft/voxel-style variant of the jump game. The camera-detected person is
rendered as a blocky Mario-styled miniatura character — each body part is a
filled rectangle (voxel block) rather than a circle or line — using Mario's
color palette (red cap, peach face, red shirt, blue overalls) with pixel eyes.
The level features a sky-blue background with pixel-style clouds and a
grass-block ground band (green top, brown dirt). Obstacles (pipes, blocks,
goombas) are rendered as voxel rectangles and start widely separated so players
can advance through levels, with spacing tightening every 10 obstacles passed.
Every 10 obstacles cleared, the player levels up; from level 2, speed increases
10% per level.

### Launch

```bash
./run_minecraft.sh
```

Or:

```bash
python3 -m src.minecraft_main
```

The game uses a themed solid background (no camera feed) and renders the
character as a small blocky Mario figure that mirrors the player's pose via
scaled landmark transformation, with each limb drawn as an oriented rectangle
block.

### Controls

- Physically **jump** to make Minecraft Mario jump and clear obstacles
- `SPACE` — Start game (from menu) / restart (after game over)
- `q` or `ESC` — Quit

### Level Progression

Same as the Mario Bros Game — every 10 obstacles cleared, the player levels
up; obstacles start very spread out and tighten with each level:

| Level | Obstacles to reach | Spawn gap range (frames) |
|-------|-------------------|-------------------------|
| 1     | 0                 | 180–280                 |
| 2     | 10                | 150–250                 |
| 3     | 20                | 130–230                 |
| 4     | 30                | 110–200                 |
| 5     | 40                | 90–170                  |
| 6+    | 50+               | 70–130                  |

In addition, game speed increases by ×1.10 from level 2 onward (same as
the base jump game).

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

## How It Works

1. **Camera capture** — OpenCV reads frames from the webcam via V4L2
2. **Multi-person pose detection** — MediaPipe PoseLandmarker (BlazePose) detects up to 4 people, each with 33 body landmarks (head, arms, torso, legs) and a segmentation mask
3. **Silhouette drawing** — Segmentation masks provide body outlines; landmarks provide articulated skeletons
4. **Character mimicry** — Smoothed landmark positions drive each character's pose in real time, with a distinct color per person
