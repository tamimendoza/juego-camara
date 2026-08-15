"""Mario Bros variant of the pose-controlled jumping game.

Pipeline:
    camera.read_frame -> BGR->RGB conversion -> mp.Image -> PoseLandmarker.detect ->
    landmark extraction -> MarioGameEngine.update -> MarioGameEngine.render -> display

The player jumps by physically raising above a baseline (shoulder landmarks).
A Mario-styled miniatura character at the bottom of the screen mirrors the
jump pose and must clear scrolling obstacles (pipes, blocks, goombas).
Obstacles start widely separated so players can advance through levels, with
spacing tightening every 5 obstacles passed. Every 5 obstacles cleared, the
player levels up; from level 2, speed increases 10% per level.

Features:
- **Lives system**: The player has 3 lives (hearts); each collision with an
  obstacle costs a life. Sky blocks in the sky can restore lives. The game
  ends when all lives are lost.
- **Background music**: GroundTheme.mp3 plays as background music during
  gameplay. InvincibilityTheme.mp3 plays when the player has 5+ coins.
- **Moving clouds**: Clouds drift across the sky at a slower speed than
  obstacles for a parallax effect.
- **Brick ground with graffiti**: The ground is rendered as orange-red bricks
  with white graffiti text.
- **Pose stability**: If the player is too close or too far from the camera
  (shoulders not fully detected), the game pauses and shows a warning.
- **Sound effects**: A coin sound plays when an obstacle is cleared; a hit
  sound plays when the character loses a life; a game-over sound plays when
  all lives are lost (via ``pygame.mixer``).
- **Double jump**: The character can perform a second jump while airborne
  for extra height, capped at ``MAX_JUMPS = 2`` to keep the character on
  screen.

Usage:
    python3 -m src.games.mario
    # or: ./run_mario_face.sh
"""

import random
from typing import List, Optional, Sequence

import cv2
import numpy as np

from ...core.silhouette import SilhouetteDrawer, MARIO_FACE, MARIO_HAT, MARIO_HAIR, MARIO_SHIRT, MARIO_OVERALL
from ...framework.jump_game import (
    JumpDetector,
    GRAVITY,
    JUMP_VELOCITY,
    JUMP_RISE_WINDOW,
    BASE_SPEED,
    SPEED_MULTIPLIER,
    MAX_LIVES,
    HEART_COLOR,
    draw_heart,
    SKY_BLOCK_SIZE,
    SKY_BLOCK_COLOR,
    SKY_BLOCK_SPAWN_INTERVAL,
    SKY_BLOCK_HEIGHT_RANGE,
    CLOUD_COLOR,
    CLOUD_SPEED_FACTOR,
    CLOUD_SPAWN_INTERVAL,
    CLOUD_SIZE_RANGE,
    POSE_WARNING_TEXT,
    POSE_WARNING_COLOR,
    MIN_SHOULDER_WIDTH,
    MAX_SHOULDER_WIDTH,
    INVINCIBILITY_THRESHOLD,
    SkyBlock,
    Cloud,
)
from ...core.sound_manager import SoundManager
from ...core.utils import LandmarkPoint
from ...core.character import mirror_points

# --- Geometry constants ---
WINDOW_NAME = "Juego Camara - Mario Bros"
RESOLUTION = (640, 480)
GROUND_Y_RATIO = 0.85  # ground sits lower, leaving room for clouds/bushes above
CHARACTER_X = 80
CHARACTER_TARGET_HEIGHT = 90
HEAD_RADIUS_MIN = 8
TOP_MARGIN = 60.0  # px the character top may not rise above the screen top
MAX_JUMP_OFFSET = max(  # highest jump offset that keeps the character on screen
    GROUND_Y_RATIO * RESOLUTION[1] - CHARACTER_TARGET_HEIGHT - TOP_MARGIN,
    1.0,
)

# --- Jump detection constants ---
JUMP_THRESHOLD = 30.0
JUMP_COOLDOWN = 8

# --- Double jump constants ---
MAX_JUMPS = 2
DOUBLE_JUMP_VELOCITY = -10.0

# --- Landmark indices (mirror game.py) ---
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24

# --- Name entry constants ---
MAX_NAME_LENGTH = 15  # max characters in the player's name buffer

# --- Level / spacing constants ---
LEVEL_INTERVAL = 5  # obstacles passed before level increments and gaps tighten
LEVEL_SPAWN_GAP_RANGES = [
    (180, 280),  # Level 1: very spacious
    (150, 250),  # Level 2
    (130, 230),  # Level 3
    (110, 200),  # Level 4
    (90, 170),   # Level 5
    (70, 130),   # Level 6+ (hard cap)
]
MAX_LEVEL = len(LEVEL_SPAWN_GAP_RANGES) - 1  # index of last range = level 6
LEVEL_UP_DISPLAY_FRAMES = 90  # show "LEVEL UP" overlay for ~1.5s at 60 FPS

# --- Obstacle dimensions ---
PIPE_WIDTH = 40
PIPE_HEIGHT = 80
BLOCK_WIDTH = 40
BLOCK_HEIGHT = 40
GOOMBA_WIDTH = 30
GOOMBA_HEIGHT = 30
OBSTACLE_TYPES = ["pipe", "block", "goomba"]

# --- Mario-themed colors (BGR) ---
SKY_COLOR = (235, 206, 135)      # sky blue (RGB 135,206,235)
CLOUD_COLOR = (255, 255, 255)    # white clouds
BUSH_COLOR = (0, 128, 0)         # green bushes
FLOWER_COLOR = (0, 0, 200)       # red flowers
GROUND_COLOR = (100, 120, 180)   # brown ground (RGB 180,120,100)
BRICK_STROKE = (60, 80, 120)     # darker brown for brick lines (RGB 120,80,60)
BLOCK_COLOR = (30, 165, 200)     # orange blocks (RGB 200,165,30)
PIPE_COLOR = (0, 180, 0)         # green pipes (RGB 0,180,0)
GOOMBA_COLOR = (0, 50, 200)      # red-brown goombas (RGB 200,50,0)
HUD_COLOR = (255, 255, 255)      # white HUD
GAME_OVER_COLOR = (0, 0, 255)    # red game over text
LEVEL_UP_COLOR = (0, 255, 255)   # yellow level-up text

# --- Graffiti constants ---
GRAFFITI_TEXT = "Familia Mendoza Silva"
GRAFFITI_COLOR = (255, 255, 255)  # white graffiti

# --- Static environment element positions ---
_CLOUD_OFFSETS = [
    (80, 80), (200, 70), (340, 90), (480, 60), (560, 85),
]
_BUSH_OFFSETS = [
    (50, 400), (150, 410), (280, 405), (420, 395), (520, 400),
]


class MarioCharacter:
    """A Mario-styled miniatura character with jump physics.

    Mirrors ``PlayerCharacter`` from ``game.py`` but renders the pose with
    Mario Bros colours (red cap, peach face, red shirt, blue overalls)
    instead of a plain stick figure. The pose landmarks still drive the
    character's posture and jump.
    """

    def __init__(
        self,
        x: int,
        ground_y: int,
        scale: float = 0.30,
    ):
        self.x = x
        self.ground_y = ground_y
        self._scale = scale

        self._vy = 0.0
        self._on_ground = True
        self._jump_offset = 0.0
        self._jump_count = 0

        self._drawer = SilhouetteDrawer()
        self._drawer.line_color = MARIO_SHIRT
        self._drawer.joint_color = MARIO_HAT
        self._drawer.silhouette_color = MARIO_SHIRT
        self._drawer.line_thickness = 1
        self._drawer.joint_radius = 3

        self._render_points: Optional[List[LandmarkPoint]] = None
        self._bbox: tuple = (0, 0, 0, 0)
        self.scale_warning = False

    def jump(self) -> bool:
        """Trigger a jump, supporting a single double-jump while airborne.

        The first jump applies ``JUMP_VELOCITY``.  A second jump (double jump)
        while airborne applies an additional ``DOUBLE_JUMP_VELOCITY`` boost.
        After ``MAX_JUMPS`` jumps the method returns ``False`` until the
        character lands and ``_jump_count`` resets.
        """
        if self._jump_count >= MAX_JUMPS:
            return False
        if self._jump_count == 0:
            self._vy = JUMP_VELOCITY
        else:
            self._vy += DOUBLE_JUMP_VELOCITY
        self._jump_count += 1
        self._on_ground = False
        return True

    def update(self, landmarks: Optional[Sequence[LandmarkPoint]] = None) -> None:
        """Apply gravity and update jump position.

        Also checks pose stability: if shoulders are not detected or the
        shoulder width is outside the acceptable range, ``scale_warning``
        is set to ``True`` so the game can pause and show a warning.
        """
        if not self._on_ground:
            self._vy += GRAVITY
            self._jump_offset += self._vy
            # Clamp the apex so the character never leaves the screen
            if self._jump_offset > MAX_JUMP_OFFSET:
                self._jump_offset = MAX_JUMP_OFFSET
            if self._jump_offset >= 0:
                self._jump_offset = 0.0
                self._vy = 0.0
                self._on_ground = True
                self._jump_count = 0

        if landmarks is not None:
            self._update_render_points(landmarks)
            self._check_pose_stability(landmarks)
        else:
            self.scale_warning = True

    def _check_pose_stability(self, landmarks: Sequence[LandmarkPoint]) -> None:
        """Set scale_warning when shoulders are missing or too close/far."""
        ls = landmarks[LEFT_SHOULDER] if len(landmarks) > LEFT_SHOULDER else None
        rs = landmarks[RIGHT_SHOULDER] if len(landmarks) > RIGHT_SHOULDER else None
        if ls is None or rs is None:
            self.scale_warning = True
        else:
            shoulder_width = abs(rs[0] - ls[0])
            if shoulder_width < MIN_SHOULDER_WIDTH or shoulder_width > MAX_SHOULDER_WIDTH:
                self.scale_warning = True
            else:
                self.scale_warning = False

    def _update_render_points(self, landmarks: Sequence[LandmarkPoint]) -> None:
        """Scale and translate pose landmarks to miniatura position.

        Centers the pose on its shoulder midpoint (or centroid if shoulders
        are occluded), scales to ``CHARACTER_TARGET_HEIGHT`` pixels tall, and
        positions the character so its bottom rests on the ground line
        (offset upward by ``_jump_offset`` when jumping).
        """
        points = list(landmarks)

        visible = [p for p in points if p is not None]
        if len(visible) < 3:
            self._render_points = None
            self._bbox = (0, 0, 0, 0)
            return

        ls = points[LEFT_SHOULDER] if len(points) > LEFT_SHOULDER else None
        rs = points[RIGHT_SHOULDER] if len(points) > RIGHT_SHOULDER else None
        if ls is not None and rs is not None:
            cx = (ls[0] + rs[0]) / 2.0
            cy = (ls[1] + rs[1]) / 2.0
        else:
            cx = sum(p[0] for p in visible) / len(visible)
            cy = sum(p[1] for p in visible) / len(visible)

        all_y = [p[1] for p in visible]
        min_y_vis = min(all_y)
        max_y_vis = max(all_y)
        pose_height = max_y_vis - min_y_vis
        if pose_height < 10:
            pose_height = 10.0

        scale = CHARACTER_TARGET_HEIGHT / pose_height

        ground_y = self.ground_y + self._jump_offset
        target_y = ground_y - (max_y_vis - cy) * scale
        target_x = self.x

        transformed: List[LandmarkPoint] = []
        min_tx = float("inf")
        max_tx = float("-inf")
        min_ty = float("inf")
        max_ty = float("-inf")

        for p in points:
            if p is None:
                transformed.append(None)
                continue
            tx = int(target_x + (p[0] - cx) * scale)
            ty = int(target_y + (p[1] - cy) * scale)
            transformed.append((tx, ty))
            min_tx = min(min_tx, tx)
            max_tx = max(max_tx, tx)
            min_ty = min(min_ty, ty)
            max_ty = max(max_ty, ty)

        self._render_points = transformed

        pad = 4
        self._bbox = (
            min_tx - pad,
            min_ty - pad,
            max_tx - min_tx + 2 * pad,
            max_ty - min_ty + 2 * pad,
        )

    @property
    def on_ground(self) -> bool:
        return self._on_ground

    @property
    def bounding_box(self) -> tuple:
        """AABB: (x, y, width, height) for collision detection."""
        return self._bbox

    def reset(self) -> None:
        """Reset to ground position."""
        self._vy = 0.0
        self._on_ground = True
        self._jump_offset = 0.0
        self._jump_count = 0
        self._render_points = None
        self._bbox = (0, 0, 0, 0)

    def render(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Draw the Mario miniatura on the frame."""
        if self._render_points is None:
            self._draw_fallback(frame)
            return

        styles = ["mario_head", "mario_body", "torso_fill"]
        self._drawer.render_character(
            frame,
            self._render_points,
            mask_binary=None,
            connections=list(connections) if connections else None,
            styles=styles,
        )

    def _draw_fallback(self, frame: np.ndarray) -> None:
        """Draw a simple static Mario figure when no pose is available."""
        cx = self.x
        cy = int(self.ground_y + self._jump_offset)
        r = HEAD_RADIUS_MIN
        # Face
        cv2.circle(frame, (cx, cy - r), r, MARIO_FACE, -1)
        # Cap
        cap_center = (cx, cy - 2 * r)
        cv2.ellipse(
            frame, cap_center, (int(r * 1.2), int(r * 0.5)),
            0, 0, 180, MARIO_HAT, -1,
        )
        # Body (shirt line)
        cv2.line(frame, (cx, cy), (cx, cy + 30), MARIO_SHIRT, max(self._drawer.line_thickness + 1, 3))


class MarioObstacle:
    """A Mario-themed obstacle moving leftward at the current game speed.

    Each obstacle has a ``type`` ("pipe", "block", "goomba") that determines
    its visual appearance and dimensions.
    """

    def __init__(
        self,
        x: int,
        ground_y: int,
        width: int,
        height: int,
        speed: float,
        obs_type: str,
        color: tuple,
    ):
        self.x = float(x)
        self.ground_y = ground_y
        self.width = width
        self.height = height
        self.speed = speed
        self.color = color
        self.type = obs_type
        self.passed = False

    def update(self) -> None:
        """Move leftward by the current speed."""
        self.x -= self.speed

    def render(self, frame: np.ndarray) -> None:
        """Draw the obstacle according to its Mario type."""
        x0 = int(self.x)
        x1 = int(self.x + self.width)
        y0 = self.ground_y - self.height
        y1 = self.ground_y

        if self.type == "pipe":
            # Green pipe with darker border
            cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
            cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 100, 0), 2)
        elif self.type == "block":
            # Orange block with question mark
            cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
            cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 0, 0), 2)
            # Question mark in the center
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            cv2.putText(frame, "?", (cx - 5, cy + 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 0), 2, cv2.LINE_AA)
        else:  # goomba
            # Red-brown enemy rectangle with darker border
            cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
            cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 30, 100), 2)
            # Eyes (small white dots)
            eye_y = y0 + self.height // 3
            cv2.circle(frame, (cx := x0 + self.width // 3, eye_y), 3, (255, 255, 255), -1)
            cv2.circle(frame, (x1 - self.width // 3, eye_y), 3, (255, 255, 255), -1)

    def off_screen(self) -> bool:
        """Check if the obstacle has moved completely off the left edge."""
        return self.x + self.width < 0

    def check_collision(self, bbox: tuple) -> bool:
        """AABB collision check. bbox = (x, y, w, h).

        Returns ``False`` once the obstacle has been marked as passed (the
        coin sound has already been scored), preventing the character from
        colliding with an obstacle that has already cleared them.
        """
        if self.passed:
            return False
        return self._aabb_overlap(
            (self.x, self.ground_y - self.height, self.width, self.height),
            bbox,
        )

    @staticmethod
    def _aabb_overlap(a: tuple, b: tuple) -> bool:
        """Return True if two AABBs (x, y, w, h) overlap."""
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return not (
            ax + aw < bx
            or bx + bw < ax
            or ay + ah < by
            or by + bh < ay
        )

    def mark_passed(self, character_x: int) -> bool:
        """If the obstacle has passed the character, mark it and return True."""
        if not self.passed and self.x + self.width < character_x:
            self.passed = True
            return True
        return False


class MarioObstacleManager:
    """Spawns Mario-themed obstacles, tracks score, level, and controls speed.

    Obstacles start widely separated (level 1) and the spawn gap tightens
    every ``LEVEL_INTERVAL`` (5) obstacles passed, up to ``MAX_LEVEL``.
    """

    def __init__(
        self,
        width: int,
        ground_y: int,
        base_speed: float = BASE_SPEED,
    ):
        self.width = width
        self.ground_y = ground_y
        self._speed = base_speed
        self._obstacles: List[MarioObstacle] = []
        self._spawn_timer = 0
        self._passed_count = 0
        self._type_index = 0  # cycles through OBSTACLE_TYPES

    @property
    def passed_count(self) -> int:
        return self._passed_count

    @property
    def level(self) -> int:
        """Current level: increments every LEVEL_INTERVAL obstacles passed."""
        return min(self._passed_count // LEVEL_INTERVAL + 1, MAX_LEVEL + 1)

    @property
    def spawn_gap_range(self) -> tuple:
        """Current spawn gap range based on the current level."""
        idx = min(self.level - 1, MAX_LEVEL)
        return LEVEL_SPAWN_GAP_RANGES[idx]

    @property
    def speed(self) -> float:
        return self._speed

    def set_speed(self, speed: float) -> None:
        """Update speed for all existing and future obstacles."""
        self._speed = speed
        for obs in self._obstacles:
            obs.speed = speed

    def update(self, character_x: int, character_bbox: tuple) -> None:
        """Update all obstacles: move, check passing, remove off-screen, spawn."""
        for obs in self._obstacles:
            obs.update()

        new_obstacles = []
        for obs in self._obstacles:
            if not obs.passed and obs.mark_passed(character_x):
                self._passed_count += 1
            if not obs.off_screen():
                new_obstacles.append(obs)
        self._obstacles = new_obstacles

        self._spawn_timer -= 1
        if self._spawn_timer <= 0:
            self._spawn()
            self._spawn_timer = random.randint(*self.spawn_gap_range)

    def _spawn(self) -> None:
        """Create a new obstacle at the right edge, cycling through types."""
        obs_type = OBSTACLE_TYPES[self._type_index % len(OBSTACLE_TYPES)]
        self._type_index += 1

        if obs_type == "pipe":
            width, height, color = PIPE_WIDTH, PIPE_HEIGHT, PIPE_COLOR
        elif obs_type == "block":
            width, height, color = BLOCK_WIDTH, BLOCK_HEIGHT, BLOCK_COLOR
        else:  # goomba
            width, height, color = GOOMBA_WIDTH, GOOMBA_HEIGHT, GOOMBA_COLOR

        obs = MarioObstacle(
            x=self.width,
            ground_y=self.ground_y,
            width=width,
            height=height,
            speed=self._speed,
            obs_type=obs_type,
            color=color,
        )
        self._obstacles.append(obs)

    def check_collisions(self, character_bbox: tuple) -> bool:
        """Return True if any obstacle collides with the character bbox.

        Removes the colliding obstacle to prevent repeated collision
        detection across consecutive frames.
        """
        for i, obs in enumerate(self._obstacles):
            if obs.check_collision(character_bbox):
                del self._obstacles[i]
                return True
        return False

    def render(self, frame: np.ndarray) -> None:
        """Draw all obstacles."""
        for obs in self._obstacles:
            obs.render(frame)

    def reset(self) -> None:
        """Clear all obstacles and reset counters."""
        self._obstacles = []
        self._spawn_timer = 0
        self._passed_count = 0
        self._type_index = 0


class MarioGameEngine:
    """Mario Bros themed game engine.

    States:
        MENU (0) -> PLAYING (1) -> GAME_OVER (2)

    Reuses the same jump-detection and physics as the base pose jump game,
    but renders a Mario Bros-style background, character, and obstacles.
    """

    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    NAME_ENTRY = 3

    def __init__(
        self,
        width: int,
        height: int,
        sound_manager: Optional[SoundManager] = None,
        score_store=None,
    ):
        self.width = width
        self.height = height
        self._ground_y = int(height * GROUND_Y_RATIO)

        self._player = MarioCharacter(CHARACTER_X, self._ground_y)
        self._obstacle_manager = MarioObstacleManager(width, self._ground_y)
        self._jump_detector = JumpDetector(
            threshold=JUMP_THRESHOLD,
            cooldown=JUMP_COOLDOWN,
        )
        self._sound_manager = sound_manager if sound_manager is not None else SoundManager()
        self._score_store = score_store

        self._state = self.MENU
        self._frame_count = 0
        self._level_up_timer = 0  # frames remaining for level-up overlay

        # Lives system
        self._lives = MAX_LIVES

        # Coin counter (accumulated across obstacles and sky blocks)
        self._coins = 0

        # Player name entry and cached leaderboard
        self._player_name = ""
        self._leaderboard = []

        # Sky blocks (life-restoring blocks in the sky)
        self._sky_blocks: List[SkyBlock] = []
        self._sky_block_timer = 0

        # Moving clouds (parallax background)
        self._clouds: List[Cloud] = []
        self._cloud_timer = 0

        # Invincibility theme state
        self._invincibility_active = False

    @property
    def player_name(self) -> str:
        """Current player's name (set at name entry)."""
        return self._player_name

    @property
    def leaderboard(self) -> list:
        """Cached Top 5 leaderboard rows, each (position, name, coins, level)."""
        return self._leaderboard

    @property
    def lives(self) -> int:
        """Current number of lives remaining (0 to MAX_LIVES)."""
        return self._lives

    @property
    def coins(self) -> int:
        """Current number of accumulated coins."""
        return self._coins

    @property
    def state(self) -> int:
        return self._state

    @property
    def state_name(self) -> str:
        return {
            self.MENU: "MENU",
            self.PLAYING: "PLAYING",
            self.GAME_OVER: "GAME_OVER",
            self.NAME_ENTRY: "NAME_ENTRY",
        }.get(
            self._state, "UNKNOWN"
        )

    @property
    def passed_count(self) -> int:
        return self._obstacle_manager.passed_count

    @property
    def level(self) -> int:
        return self._obstacle_manager.level

    @property
    def speed(self) -> float:
        """Current game speed, scaled by level (increases from level 2)."""
        multiplier = SPEED_MULTIPLIER ** (self._obstacle_manager.level - 1)
        return BASE_SPEED * multiplier

    def start(self) -> None:
        """Transition to PLAYING state and start background music."""
        self.reset()
        self._state = self.PLAYING
        self._sound_manager.play_background_music()

    def _begin_playing(self) -> None:
        """Start a game from NAME_ENTRY, keeping the entered player name.

        The gameplay state is reset fresh (obstacles, clouds, lives, coins),
        then the entered name is restored and PLAYING begins.
        """
        name = self._player_name.strip()
        self.reset()
        self._player_name = name
        self._state = self.PLAYING
        self._sound_manager.play_background_music()

    def reset(self) -> None:
        """Reset all game state to initial values."""
        self._player.reset()
        self._obstacle_manager.reset()
        self._jump_detector.reset()
        self._frame_count = 0
        self._level_up_timer = 0
        self._state = self.MENU

        # Reset lives, sky blocks, clouds, and invincibility
        self._lives = MAX_LIVES
        self._coins = 0
        self._sky_blocks = []
        self._sky_block_timer = 0
        self._clouds = []
        self._seed_clouds(self.speed)
        self._cloud_timer = 0
        self._invincibility_active = False
        self._sound_manager.stop_invincibility_theme()

        # Reset name buffer and cached leaderboard
        self._player_name = ""
        self._leaderboard = []

    def _save_score(self) -> None:
        """Persist the current player's best score and cache the Top 5.

        Only writes when a score store is configured and a player name is set.
        """
        if self._score_store is not None and self._player_name:
            self._score_store.upsert_best(
                self._player_name, self._coins, self.level
            )
            self._leaderboard = self._score_store.top_scores(5)

    def update(
        self,
        landmarks: Optional[Sequence[LandmarkPoint]] = None,
        connections: Optional[Sequence[tuple]] = None,
    ) -> None:
        """Advance the game by one frame."""
        self._frame_count += 1

        if self._state == self.MENU:
            return

        if self._state == self.NAME_ENTRY:
            return

        if self._state == self.PLAYING:
            self._update_playing(landmarks, connections)
        # GAME_OVER: frozen state

    def _update_playing(
        self,
        landmarks: Optional[Sequence[LandmarkPoint]],
        connections: Optional[Sequence[tuple]],
    ) -> None:
        # Mirror the pose so the miniatura character behaves like the player's
        # mirror image: pointing forward along the character's path stays
        # forward, instead of being rendered in reverse.
        if landmarks is not None:
            landmarks = mirror_points(landmarks, self.width)

        # 1. Update player physics (includes pose stability check)
        self._player.update(landmarks)

        # 2. Pose stability: pause game if pose not fully detected
        if self._player.scale_warning:
            self._sound_manager.play_pose_warning()
            return

        # 3. Detect jump from pose
        if landmarks is not None:
            if self._jump_detector.update(landmarks):
                self._player.jump()

        # 4. Update speed based on score
        current_speed = self.speed
        self._obstacle_manager.set_speed(current_speed)

        # 5. Update obstacles (handles level-up detection)
        old_level = self._obstacle_manager.level
        old_passed_count = self._obstacle_manager.passed_count
        self._obstacle_manager.update(
            CHARACTER_X, self._player.bounding_box
        )
        if self._obstacle_manager.passed_count > old_passed_count:
            self._coins += 1
            self._sound_manager.play_coin()
        if self._obstacle_manager.level > old_level:
            self._level_up_timer = LEVEL_UP_DISPLAY_FRAMES

        # 6. Update sky blocks
        self._update_sky_blocks(current_speed)

        # 7. Update clouds
        self._update_clouds(current_speed)

        # 8. Invincibility theme: play when score >= threshold
        if self._obstacle_manager.passed_count >= INVINCIBILITY_THRESHOLD:
            if not self._invincibility_active:
                self._invincibility_active = True
                self._sound_manager.play_invincibility_theme()
        else:
            if self._invincibility_active:
                self._invincibility_active = False
                self._sound_manager.stop_invincibility_theme()

        # 9. Collision check - lose a life instead of immediate game over
        if self._obstacle_manager.check_collisions(self._player.bounding_box):
            self._lives -= 1
            if self._lives > 0:
                self._sound_manager.play_hit()
            else:
                self._sound_manager.play_game_over()
                self._state = self.GAME_OVER
                self._save_score()

        # 10. Decrement level-up timer
        if self._level_up_timer > 0:
            self._level_up_timer -= 1

    def _update_sky_blocks(self, current_speed: float) -> None:
        """Update sky blocks: move, check collisions, spawn new ones."""
        for block in self._sky_blocks:
            block.update()

        char_bbox = self._player.bounding_box
        for block in self._sky_blocks:
            if not block.collected and block.check_collision(char_bbox):
                if self._lives < MAX_LIVES:
                    self._lives += 1
                    self._sound_manager.play_coin()
                block.collected = True

        self._sky_blocks = [
            b for b in self._sky_blocks
            if not b.off_screen() and not b.collected
        ]

        self._sky_block_timer -= 1
        if self._sky_block_timer <= 0:
            self._spawn_sky_block(current_speed)
            self._sky_block_timer = random.randint(*SKY_BLOCK_SPAWN_INTERVAL)

    def _spawn_sky_block(self, current_speed: float) -> None:
        """Create a new sky block at the right edge."""
        y = random.randint(*SKY_BLOCK_HEIGHT_RANGE)
        block = SkyBlock(
            x=self.width,
            y=y,
            size=SKY_BLOCK_SIZE,
            color=SKY_BLOCK_COLOR,
            speed=current_speed,
        )
        self._sky_blocks.append(block)

    def _update_clouds(self, current_speed: float) -> None:
        """Update clouds: move and spawn new ones."""
        for cloud in self._clouds:
            cloud.update()

        self._clouds = [c for c in self._clouds if not c.off_screen()]

        self._cloud_timer -= 1
        if self._cloud_timer <= 0:
            self._spawn_cloud(current_speed)
            self._cloud_timer = random.randint(*CLOUD_SPAWN_INTERVAL)

    def _spawn_cloud(self, current_speed: float) -> None:
        """Create a new cloud at the right edge."""
        width = random.randint(*CLOUD_SIZE_RANGE)
        height = width * 2 // 3
        y = random.randint(40, self._ground_y // 2)
        cloud = Cloud(
            x=self.width,
            y=y,
            width=width,
            height=height,
            color=CLOUD_COLOR,
            speed=current_speed,
        )
        self._clouds.append(cloud)

    def _seed_clouds(self, current_speed: float) -> None:
        """Populate the moving cloud layer across the sky at game start."""
        for _ in range(5):
            width = random.randint(*CLOUD_SIZE_RANGE)
            height = width * 2 // 3
            y = random.randint(40, self._ground_y // 2)
            x = int(self.width * random.uniform(0.15, 0.95))
            cloud = Cloud(
                x=x,
                y=y,
                width=width,
                height=height,
                color=CLOUD_COLOR,
                speed=current_speed,
            )
            self._clouds.append(cloud)

    def render(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render the current game state onto the frame."""
        if self._state == self.MENU:
            self._render_menu(frame)
        elif self._state == self.NAME_ENTRY:
            self._render_name_entry(frame)
        elif self._state == self.PLAYING:
            self._render_game(frame, connections)
        elif self._state == self.GAME_OVER:
            self._render_game_over(frame, connections)

    def _render_static_environment(
        self, frame: np.ndarray, draw_clouds: bool = True,
        graffiti_y: Optional[int] = None,
    ) -> None:
        """Draw static clouds, bushes, and ground with graffiti (no sky fill).

        Args:
            frame: The display canvas.
            draw_clouds: When False, static clouds are skipped (bushes, flowers,
                ground, and graffiti are still drawn). During gameplay the sky is
                populated only by the moving cloud layer.
            graffiti_y: Baseline y for the graffiti text. When None, the text is
                drawn just above the ground line (``ground_top - 10``); when a
                value is given, the text baseline is placed at that y (used to
                draw the graffiti over the bricks).
        """
        # Static clouds (only for menu / game-over backgrounds)
        if draw_clouds:
            for cx, cy in _CLOUD_OFFSETS:
                cv2.ellipse(frame, (cx, cy), (30, 15), 0, 0, 360, CLOUD_COLOR, -1)
                cv2.ellipse(frame, (cx - 25, cy + 5), (20, 12), 0, 0, 360, CLOUD_COLOR, -1)
                cv2.ellipse(frame, (cx + 25, cy + 5), (20, 12), 0, 0, 360, CLOUD_COLOR, -1)

        # Bushes
        for bx, by in _BUSH_OFFSETS:
            cv2.ellipse(frame, (bx, by), (25, 12), 0, 0, 360, BUSH_COLOR, -1)
            cv2.ellipse(frame, (bx - 18, by + 4), (15, 9), 0, 0, 360, BUSH_COLOR, -1)
            cv2.ellipse(frame, (bx + 18, by + 4), (15, 9), 0, 0, 360, BUSH_COLOR, -1)
            # Red flower
            cv2.circle(frame, (bx, by - 4), 4, FLOWER_COLOR, -1)

        # Ground (brown band with brick pattern and graffiti)
        ground_top = self._ground_y
        cv2.rectangle(frame, (0, ground_top), (self.width, self.height), GROUND_COLOR, -1)
        # Brick pattern
        brick_w = 20
        brick_h = 10
        for y in range(ground_top, self.height, brick_h):
            for x in range(0, self.width, brick_w):
                cv2.rectangle(frame, (x + 2, y + 2), (x + brick_w - 2, y + brick_h - 2),
                              BRICK_STROKE, 1)
        # Graffiti text
        graffiti_baseline = ground_top - 10 if graffiti_y is None else graffiti_y
        cv2.putText(
            frame,
            GRAFFITI_TEXT,
            (self.width // 2 - 100, graffiti_baseline),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            GRAFFITI_COLOR,
            1,
            cv2.LINE_AA,
        )

    def _render_game(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render playing game: sky background + clouds + sky blocks + character + obstacles + ground + HUD."""
        # Sky blue background (de-identified, no camera feed)
        frame[:] = (200, 230, 255)  # light sky blue (BGR)

        # Render moving clouds (parallax background)
        for cloud in self._clouds:
            cloud.render(frame)

        # Render sky blocks
        for block in self._sky_blocks:
            block.render(frame)

        # Render static environment (bushes, ground with graffiti; no static clouds)
        self._render_static_environment(frame, draw_clouds=False)

        # Render obstacles
        self._obstacle_manager.render(frame)

        # Render character
        self._player.render(frame, connections)

        # HUD (hearts, level, score, speed)
        self._draw_hud(frame)

        # Pose warning text
        if self._player.scale_warning:
            cv2.putText(
                frame,
                POSE_WARNING_TEXT,
                (self.width // 2 - 180, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                POSE_WARNING_COLOR,
                2,
                cv2.LINE_AA,
            )

        # Level-up overlay
        if self._level_up_timer > 0:
            self._render_level_up(frame)

    def _render_menu(self, frame: np.ndarray) -> None:
        """Render the Mario-themed menu screen."""
        frame[:] = SKY_COLOR
        self._render_static_environment(frame)

        # Darken slightly for menu overlay
        overlay = frame.copy()
        overlay[:] = (overlay * 0.5).astype(overlay.dtype)
        frame[:] = overlay

        cx = self.width // 2
        cv2.putText(
            frame, "MARIO POSE JUMP",
            (cx - 120, self.height // 2 - 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, HUD_COLOR, 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame, "Jump to start",
            (cx - 80, self.height // 2 + 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, "Press SPACE to start",
            (cx - 100, self.height // 2 + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

    def _render_name_entry(self, frame: np.ndarray) -> None:
        """Render the name-entry prompt (base fallback; Face variant overrides)."""
        self._render_menu(frame)

    def _render_game_over(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render game over screen (frozen game frame + overlay)."""
        self._render_game(frame, connections)
        # Dim the game slightly
        frame[:] = (frame * 0.4).astype(frame.dtype)

        speed_mult = SPEED_MULTIPLIER ** (self._obstacle_manager.level - 1)

        cv2.putText(
            frame, "GAME OVER",
            (self.width // 2 - 80, self.height // 2 - 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, GAME_OVER_COLOR, 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Score: {self.passed_count}",
            (self.width // 2 - 40, self.height // 2 + 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUD_COLOR, 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Level: {self._obstacle_manager.level}",
            (self.width // 2 - 40, self.height // 2 + 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Speed: {speed_mult:.1f}x",
            (self.width // 2 - 40, self.height // 2 + 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, "Press SPACE to restart",
            (self.width // 2 - 90, self.height // 2 + 110),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

    def _render_level_up(self, frame: np.ndarray) -> None:
        """Render a temporary 'LEVEL UP' overlay."""
        font_scale = 1.2
        thickness = 3
        text = f"LEVEL {self._obstacle_manager.level} !"
        (w, h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        cx = self.width // 2
        cv2.putText(
            frame, text,
            (cx - w // 2, self.height // 2 - 40),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, LEVEL_UP_COLOR, thickness, cv2.LINE_AA,
        )

    def _draw_hearts(self, frame: np.ndarray) -> None:
        """Draw the remaining lives as red hearts (gray when lost)."""
        for i in range(MAX_LIVES):
            color = HEART_COLOR if i < self._lives else (100, 100, 100)
            cx = self.width - 35 - i * 28
            cy = 25
            draw_heart(frame, (cx, cy), 22, color)

    def _draw_hud(self, frame: np.ndarray) -> None:
        """Draw score, level, speed, and hearts on the frame."""
        speed_mult = SPEED_MULTIPLIER ** (self._obstacle_manager.level - 1)
        self._draw_hearts(frame)
        cv2.putText(
            frame, f"Monedas: {self.passed_count}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUD_COLOR, 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Nivel: {self._obstacle_manager.level}",
            (10, 48),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Velocidad: {speed_mult:.1f}x",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

    def handle_key(self, key: int) -> None:
        """Handle keyboard input for game control."""
        if self._state == self.NAME_ENTRY:
            self._handle_name_entry_key(key)
            return

        if key == ord(" "):
            if self._state == self.MENU:
                self.start()
            elif self._state == self.GAME_OVER:
                self.start()
        elif key == ord("q") or key == 27:
            pass  # handled by caller for exit

    def _handle_name_entry_key(self, key: int) -> None:
        """Handle text input while in the NAME_ENTRY state."""
        if key == 8:  # BACKSPACE
            self._player_name = self._player_name[:-1]
        elif key in (13, 10):  # ENTER
            if self._player_name.strip():
                self._begin_playing()
            # Empty name: stay in NAME_ENTRY
        elif 32 <= key <= 126 and len(self._player_name) < MAX_NAME_LENGTH:
            self._player_name += chr(key)
        # q / ESC are handled by the caller for exit

    def close(self) -> None:
        """Clean up resources (sound manager and score store)."""
        self._sound_manager.stop_background_music()
        self._sound_manager.close()
        if self._score_store is not None:
            self._score_store.close()
