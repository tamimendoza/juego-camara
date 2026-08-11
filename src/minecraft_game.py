"""Minecraft-style Mario Bros variant of the pose-controlled jumping game.

Pipeline:
    camera.read_frame -> BGR->RGB conversion -> mp.Image -> PoseLandmarker.detect ->
    landmark extraction -> MinecraftGameEngine.update -> MinecraftGameEngine.render -> display

The player jumps by physically raising above a baseline (shoulder landmarks).
The pose-driven character is rendered in a **Minecraft voxel style** — each body
part is a filled rectangle (block) rather than a circle or line — using Mario's
color palette (red cap, peach face, red shirt, blue overalls) against a
Minecraft-themed background (sky blue, pixel clouds, grass-block ground).

Obstacles (pipes, blocks, goombas) start widely separated so players can advance
through levels, with spacing tightening every 5 obstacles passed. Every 5
obstacles cleared, the player levels up; from level 2, speed increases 10% per
level. The player has 3 lives (hearts); losing all lives ends the game.

Usage:
    python3 -m src.minecraft_main
    # or: ./run_minecraft.sh
"""

import random
from typing import List, Optional, Sequence

import cv2
import numpy as np

from .silhouette import (
    SilhouetteDrawer,
    MARIO_FACE, MARIO_HAT, MARIO_HAIR,
    MARIO_SHIRT, MARIO_OVERALL,
    MC_SKY, MC_GRASS_TOP, MC_DIRT, MC_CLOUD, MC_BLOCK_BORDER, MC_EYE,
)
from .game import (
    JumpDetector,
    GRAVITY,
    JUMP_VELOCITY,
    BASE_SPEED,
    SPEED_MULTIPLIER,
    MAX_LIVES,
    HEART_COLOR,
    SKY_BLOCK_SIZE,
    SKY_BLOCK_COLOR,
    SKY_BLOCK_SPEED_FACTOR,
    SKY_BLOCK_SPAWN_INTERVAL,
    SKY_BLOCK_SIZE_RANGE,
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
from .sound_manager import SoundManager
from .utils import LandmarkPoint
from .character import mirror_points

# --- Geometry constants ---
WINDOW_NAME = "Juego Camara - Minecraft Mario"
RESOLUTION = (640, 480)
GROUND_Y_RATIO = 0.85  # ground sits lower, leaving room for clouds above
CHARACTER_X = 80
CHARACTER_TARGET_HEIGHT = 110  # slightly taller than Mario variant (90) for block visibility
HEAD_BLOCK_MIN = 18
TOP_MARGIN = 60.0  # px the character top may not rise above the screen top
MAX_JUMP_OFFSET = max(  # highest jump offset that keeps the character on screen
    GROUND_Y_RATIO * RESOLUTION[1] - CHARACTER_TARGET_HEIGHT - TOP_MARGIN,
    1.0,
)

# --- Jump detection constants ---
JUMP_THRESHOLD = 30.0
JUMP_COOLDOWN = 8
BASELINE_EMA_ALPHA = 0.05

# --- Double jump constants ---
MAX_JUMPS = 2
DOUBLE_JUMP_VELOCITY = -10.0

# --- Landmark indices (mirror game.py) ---
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_HEEL = 27
RIGHT_HEEL = 28

# --- Scaling constants ---
# Normalise pose height to CHARACTER_TARGET_HEIGHT, but cap the scale so the
# character does NOT enlarge when only partial landmarks are detected (e.g.
# when the user is far from the camera or some joints are occluded).
NOMINAL_BODY_HEIGHT = 200.0  # expected full-body landmark height in 640×480
MAX_SCALE = CHARACTER_TARGET_HEIGHT / NOMINAL_BODY_HEIGHT  # ~0.55

# --- Detection-quality constants ---
# Shoulder width range (in pixels) that indicates the user is at an acceptable
# distance from the camera. Outside this range the character stays still and a
# warning message is shown at the top of the screen.
MIN_SHOULDER_WIDTH = 30
MAX_SHOULDER_WIDTH = 250

# Maximum limb extension from joints (pixels) — limits how far arms/legs can
# reach so the character never "desfigurationa" (deforms).
MAX_ARM_EXTENSION = 35
MAX_LEG_EXTENSION = 45

# --- Block rendering constants ---
BLOCK_LINE_WIDTH = 3  # thickness for oriented-rect limb blocks
BLOCK_BORDER_WIDTH = 1  # outline for each block

# --- Level / spacing constants ---
LEVEL_INTERVAL = 5
LEVEL_SPAWN_GAP_RANGES = [
    (180, 280),  # Level 1: very spacious
    (150, 250),  # Level 2
    (130, 230),  # Level 3
    (110, 200),  # Level 4
    (90, 170),   # Level 5
    (70, 130),   # Level 6+ (hard cap)
]
MAX_LEVEL = len(LEVEL_SPAWN_GAP_RANGES) - 1
LEVEL_UP_DISPLAY_FRAMES = 90

# --- Obstacle dimensions ---
PIPE_WIDTH = 40
PIPE_HEIGHT = 80
BLOCK_WIDTH = 40
BLOCK_HEIGHT = 40
GOOMBA_WIDTH = 30
GOOMBA_HEIGHT = 30
OBSTACLE_TYPES = ["pipe", "block", "goomba"]

# --- Minecraft-themed colors (BGR) ---
SKY_COLOR = MC_SKY
CLOUD_COLOR = MC_CLOUD
GRASS_COLOR = MC_GRASS_TOP
DIRT_COLOR = MC_DIRT
BRICK_COLOR = (0, 128, 255)  # orange-red bricks (BGR) — shared ground color
HUD_COLOR = (255, 255, 255)     # white HUD
GAME_OVER_COLOR = (0, 0, 255)   # red game over text
LEVEL_UP_COLOR = (0, 255, 255)  # yellow level-up text

# Reuse Mario obstacle colors (they look fine as Minecraft blocks too)
PIPE_COLOR = (0, 180, 0)        # green pipes
BLOCK_COLOR = (30, 165, 200)    # orange blocks
GOOMBA_COLOR = (0, 50, 200)     # red-brown goombas

# --- Graffiti constants ---
GRAFFITI_TEXT = "MC"
GRAFFITI_COLOR = (255, 255, 255)  # white graffiti text

# --- Sky / cloud rendering constants ---
SKY_BLUE = (200, 230, 255)  # light sky blue for playing background

# --- Static environment element positions ---
_CLOUD_OFFSETS = [
    (80, 80), (200, 70), (340, 90), (480, 60), (560, 85),
]


class MinecraftMarioCharacter:
    """A Minecraft voxel-styled Mario miniatura with jump physics.

    Mirrors ``MarioCharacter`` from ``mario_game.py`` but renders the pose with
    rectangular blocks (``minecraft_head`` / ``minecraft_body`` styles) instead
    of smooth circles/lines.  Each body part is a filled rectangle oriented
    along the limb direction, giving the blocky Minecraft "voxel" look.
    """

    def __init__(
        self,
        x: int,
        ground_y: int,
        scale: float = 0.35,
    ):
        self.x = x
        self.ground_y = ground_y
        self._scale = scale

        self._vy = 0.0
        self._on_ground = True
        self._jump_offset = 0.0
        self._jump_count = 0

        self._drawer = SilhouetteDrawer()
        self._drawer.line_color = MARIO_HAT
        self._drawer.joint_color = MARIO_HAT
        self._drawer.silhouette_color = MARIO_SHIRT
        self._drawer.line_thickness = BLOCK_LINE_WIDTH
        self._drawer.joint_radius = 2

        self._render_points: Optional[List[LandmarkPoint]] = None
        self._bbox: tuple = (0, 0, 0, 0)
        self.min_visible = 5  # minimum landmarks required to update pose
        self._scale_warning = False  # True when user too close/far → show warning

    def jump(self) -> bool:
        """Trigger a jump, supporting double jump while airborne."""
        if self._jump_count >= MAX_JUMPS:
            return False
        if self._jump_count == 0:
            self._vy = JUMP_VELOCITY
        else:
            self._vy += DOUBLE_JUMP_VELOCITY
        self._jump_count += 1
        self._on_ground = False
        return True

    @property
    def scale_warning(self) -> bool:
        """True when the pose quality is too poor for reliable rendering."""
        return self._scale_warning

    def update(self, landmarks: Optional[Sequence[LandmarkPoint]] = None) -> None:
        """Apply gravity and update jump position.

        When landmarks are too few or the detected scale is out of range
        (user too close / too far), the character keeps its last known pose
        and ``scale_warning`` is set so the game can show a message.
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
            visible = [p for p in landmarks if p is not None]
            if len(visible) >= self.min_visible:
                self._update_render_points(landmarks)
            # When too few landmarks are visible, keep the last known pose so
            # the character remains still ("quieto") rather than jumping around.

    def _update_render_points(self, landmarks: Sequence[LandmarkPoint]) -> None:
        """Map pose landmarks to a fixed-size voxel skeleton.

        The character is scaled to ``CHARACTER_TARGET_HEIGHT`` pixels tall,
        capped by ``MAX_SCALE`` so it does NOT enlarge ("ampliarse"). If the
        shoulder width falls outside ``[MIN_SHOULDER_WIDTH,
        MAX_SHOULDER_WIDTH]`` the character is NOT updated (stays still) and a
        scale warning is activated.

        After scaling, limb endpoints (wrists, heels) are clamped to a maximum
        extension from their shoulder/hip joints so the character's body never
        deforms — only arms and legs move, within a limited range.
        """
        points = list(landmarks)

        visible = [p for p in points if p is not None]
        if len(visible) < self.min_visible:
            return  # keep last known pose (character stays "quieto")

        ls = points[LEFT_SHOULDER] if len(points) > LEFT_SHOULDER else None
        rs = points[RIGHT_SHOULDER] if len(points) > RIGHT_SHOULDER else None
        if ls is None or rs is None:
            return

        # Detection-quality check: shoulder width must be in acceptable range
        shoulder_width = max(
            ((ls[0] - rs[0]) ** 2 + (ls[1] - rs[1]) ** 2) ** 0.5, 1
        )
        if shoulder_width < MIN_SHOULDER_WIDTH or shoulder_width > MAX_SHOULDER_WIDTH:
            self._scale_warning = True
            return  # user too close / too far — keep character still
        self._scale_warning = False

        if ls is not None and rs is not None:
            cx = (ls[0] + rs[0]) / 2.0
            cy = (ls[1] + rs[1]) / 2.0
        else:
            cx = sum(p[0] for p in visible) / len(visible)
            cy = sum(p[1] for p in visible) / len(visible)

        all_y = [p[1] for p in visible]
        max_y_vis = max(all_y)
        pose_height = max_y_vis - min(all_y)

        # Scale to target height, capped to prevent "ampliarse" (enlargement)
        scale = CHARACTER_TARGET_HEIGHT / max(pose_height, 10.0)
        scale = min(scale, MAX_SCALE)

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

        # Constrain limb endpoints to prevent character deformation.
        transformed = self._constrain_limbs(transformed)

        # Recompute bbox after constraints
        min_tx = float("inf")
        max_tx = float("-inf")
        min_ty = float("inf")
        max_ty = float("-inf")
        for p in transformed:
            if p is None:
                continue
            min_tx = min(min_tx, p[0])
            max_tx = max(max_tx, p[0])
            min_ty = min(min_ty, p[1])
            max_ty = max(max_ty, p[1])

        if min_tx == float("inf"):
            self._render_points = None
            self._bbox = (0, 0, 0, 0)
            return

        self._render_points = transformed

        pad = 4
        self._bbox = (
            min_tx - pad,
            min_ty - pad,
            max_tx - min_tx + 2 * pad,
            max_ty - min_ty + 2 * pad,
        )

    def _constrain_limbs(
        self, points: List[LandmarkPoint]
    ) -> List[LandmarkPoint]:
        """Clamp wrist/heel positions to a max distance from shoulder/hip joints.

        Prevents the character from deforming — arms and legs can only extend
        within a limited range, keeping the body proportional.
        """
        result = list(points)

        # Left arm: wrist (15) clamped from left shoulder (11)
        ls_pt = result[LEFT_SHOULDER] if len(result) > LEFT_SHOULDER else None
        lw_pt = result[15] if len(result) > 15 else None
        if ls_pt is not None and lw_pt is not None:
            result[15] = self._clamp_endpoint(ls_pt, lw_pt, MAX_ARM_EXTENSION)

        # Right arm: wrist (16) clamped from right shoulder (12)
        rs_pt = result[RIGHT_SHOULDER] if len(result) > RIGHT_SHOULDER else None
        rw_pt = result[16] if len(result) > 16 else None
        if rs_pt is not None and rw_pt is not None:
            result[16] = self._clamp_endpoint(rs_pt, rw_pt, MAX_ARM_EXTENSION)

        # Left leg: heel (27) clamped from left hip (23)
        lh_pt = result[LEFT_HIP] if len(result) > LEFT_HIP else None
        lhz_pt = result[LEFT_HEEL] if len(result) > LEFT_HEEL else None
        if lh_pt is not None and lhz_pt is not None:
            result[LEFT_HEEL] = self._clamp_endpoint(
                lh_pt, lhz_pt, MAX_LEG_EXTENSION
            )

        # Right leg: heel (28) clamped from right hip (24)
        rh_pt = result[RIGHT_HIP] if len(result) > RIGHT_HIP else None
        rhz_pt = result[RIGHT_HEEL] if len(result) > RIGHT_HEEL else None
        if rh_pt is not None and rhz_pt is not None:
            result[RIGHT_HEEL] = self._clamp_endpoint(
                rh_pt, rhz_pt, MAX_LEG_EXTENSION
            )

        return result

    @staticmethod
    def _clamp_endpoint(
        joint: LandmarkPoint,
        endpoint: LandmarkPoint,
        max_dist: int,
    ) -> LandmarkPoint:
        """Clamp *endpoint* to at most *max_dist* pixels from *joint*."""
        dx = endpoint[0] - joint[0]
        dy = endpoint[1] - joint[1]
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist <= max_dist or dist < 1:
            return endpoint
        return (
            int(joint[0] + dx / dist * max_dist),
            int(joint[1] + dy / dist * max_dist),
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
        """Draw the Minecraft voxel Mario miniatura on the frame."""
        if self._render_points is None:
            self._draw_fallback(frame)
            return

        styles = ["minecraft_head", "minecraft_body"]
        self._drawer.render_character(
            frame,
            self._render_points,
            mask_binary=None,
            connections=list(connections) if connections else None,
            styles=styles,
        )

    def _draw_fallback(self, frame: np.ndarray) -> None:
        """Draw a simple static Minecraft Mario figure when no pose is available."""
        cx = self.x
        cy = int(self.ground_y + self._jump_offset)
        block = HEAD_BLOCK_MIN

        # Face block (peach)
        cv2.rectangle(
            frame,
            (cx - block // 2, cy),
            (cx + block // 2, cy + block),
            MARIO_FACE, -1,
        )
        # Cap block (red) on top
        cv2.rectangle(
            frame,
            (cx - block // 2, cy - block),
            (cx + block // 2, cy),
            MARIO_HAT, -1,
        )
        # Pixel eyes
        eye_size = max(block // 7, 2)
        eye_y = cy + block // 3
        cv2.rectangle(
            frame,
            (cx - 2 * eye_size, eye_y),
            (cx - eye_size, eye_y + eye_size),
            MC_EYE, -1,
        )
        cv2.rectangle(
            frame,
            (cx + eye_size, eye_y),
            (cx + 2 * eye_size, eye_y + eye_size),
            MC_EYE, -1,
        )
        # Block borders
        cv2.rectangle(
            frame,
            (cx - block // 2, cy - block),
            (cx + block // 2, cy + block),
            MC_BLOCK_BORDER, 2,
        )

        # Torso block (red shirt)
        cv2.rectangle(
            frame,
            (cx - block // 2, cy + block),
            (cx + block // 2, cy + block + 20),
            MARIO_SHIRT, -1,
        )
        cv2.rectangle(
            frame,
            (cx - block // 2, cy + block),
            (cx + block // 2, cy + block + 20),
            MC_BLOCK_BORDER, 1,
        )
        # Leg blocks (blue overalls)
        leg_w = block // 2
        cv2.rectangle(
            frame,
            (cx - block, cy + block + 20),
            (cx - block + leg_w, cy + block + 40),
            MARIO_OVERALL, -1,
        )
        cv2.rectangle(
            frame,
            (cx, cy + block + 20),
            (cx + leg_w, cy + block + 40),
            MARIO_OVERALL, -1,
        )


class MinecraftObstacle:
    """A Minecraft-themed obstacle moving leftward at the current game speed.

    Each obstacle has a ``type`` ("pipe", "block", "goomba") rendered as a
    voxel-style filled rectangle with a dark border.
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
        """Draw the obstacle as a voxel-style rectangle with border."""
        x0 = int(self.x)
        x1 = int(self.x + self.width)
        y0 = self.ground_y - self.height
        y1 = self.ground_y

        if self.type == "pipe":
            cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
            cv2.rectangle(frame, (x0, y0), (x1, y1), MC_BLOCK_BORDER, BLOCK_BORDER_WIDTH)
        elif self.type == "block":
            cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
            cv2.rectangle(frame, (x0, y0), (x1, y1), MC_BLOCK_BORDER, BLOCK_BORDER_WIDTH)
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            cv2.putText(frame, "?", (cx - 5, cy + 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, MC_BLOCK_BORDER, 2, cv2.LINE_AA)
        else:  # goomba
            cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
            cv2.rectangle(frame, (x0, y0), (x1, y1), MC_BLOCK_BORDER, BLOCK_BORDER_WIDTH)
            eye_y = y0 + self.height // 3
            cv2.circle(frame, (x0 + self.width // 3, eye_y), 3, CLOUD_COLOR, -1)
            cv2.circle(frame, (x1 - self.width // 3, eye_y), 3, CLOUD_COLOR, -1)

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


class MinecraftObstacleManager:
    """Spawns Minecraft-themed obstacles, tracks score, level, and controls speed.

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
        self._obstacles: List[MinecraftObstacle] = []
        self._spawn_timer = 0
        self._passed_count = 0
        self._type_index = 0

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

        obs = MinecraftObstacle(
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


class MinecraftGameEngine:
    """Minecraft voxel-style Mario Bros game engine.

    States:
        MENU (0) -> PLAYING (1) -> GAME_OVER (2)

    Reuses the same jump-detection and physics as the Mario Bros variant,
    but renders a Minecraft-themed background, blocky character, and voxel
    obstacles.
    """

    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

    def __init__(self, width: int, height: int, sound_manager: Optional[SoundManager] = None):
        self.width = width
        self.height = height
        self._ground_y = int(height * GROUND_Y_RATIO)

        self._player = MinecraftMarioCharacter(CHARACTER_X, self._ground_y)
        self._obstacle_manager = MinecraftObstacleManager(width, self._ground_y)
        self._jump_detector = JumpDetector(
            threshold=JUMP_THRESHOLD,
            cooldown=JUMP_COOLDOWN,
            ema_alpha=BASELINE_EMA_ALPHA,
        )
        self._sound_manager = sound_manager if sound_manager is not None else SoundManager()

        self._state = self.MENU
        self._frame_count = 0
        self._level_up_timer = 0

        # Lives system
        self._lives = MAX_LIVES

        # Sky blocks (life-restoring blocks in the sky)
        self._sky_blocks: List[SkyBlock] = []
        self._sky_block_timer = 0

        # Moving clouds (parallax background)
        self._clouds: List[Cloud] = []
        self._cloud_timer = 0

        # Invincibility theme state
        self._invincibility_active = False

    @property
    def lives(self) -> int:
        """Current number of lives remaining (0 to MAX_LIVES)."""
        return self._lives

    @property
    def state(self) -> int:
        return self._state

    @property
    def state_name(self) -> str:
        return {self.MENU: "MENU", self.PLAYING: "PLAYING", self.GAME_OVER: "GAME_OVER"}.get(
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
        self._sky_blocks = []
        self._sky_block_timer = 0
        self._clouds = []
        self._cloud_timer = 0
        self._invincibility_active = False
        self._sound_manager.stop_invincibility_theme()

    def close(self) -> None:
        """Clean up resources (sound manager)."""
        self._sound_manager.stop_background_music()
        self._sound_manager.close()

    def update(
        self,
        landmarks: Optional[Sequence[LandmarkPoint]] = None,
        connections: Optional[Sequence[tuple]] = None,
    ) -> None:
        """Advance the game by one frame."""
        self._frame_count += 1

        if self._state == self.MENU:
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

        # 1. Update player physics
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

        # 5. Update sky blocks (life-restoring blocks)
        self._update_sky_blocks(current_speed)

        # 6. Update moving clouds (parallax background)
        self._update_clouds(current_speed)

        # 7. Update obstacles (handles level-up detection)
        old_level = self._obstacle_manager.level
        old_passed = self._obstacle_manager.passed_count
        self._obstacle_manager.update(
            CHARACTER_X, self._player.bounding_box
        )
        if self._obstacle_manager.passed_count > old_passed:
            self._sound_manager.play_coin()
        if self._obstacle_manager.level > old_level:
            self._level_up_timer = LEVEL_UP_DISPLAY_FRAMES

        # 8. Check sky block collection (restore life)
        self._check_sky_block_collection()

        # 9. Invincibility theme: play when score reaches threshold
        if (
            not self._invincibility_active
            and self._obstacle_manager.passed_count >= INVINCIBILITY_THRESHOLD
        ):
            self._invincibility_active = True
            self._sound_manager.play_invincibility_theme()

        # 10. Collision check — lose a life instead of immediate game over
        if self._obstacle_manager.check_collisions(self._player.bounding_box):
            self._lives -= 1
            if self._lives > 0:
                self._sound_manager.play_hit()
            else:
                self._sound_manager.play_game_over()
                self._state = self.GAME_OVER

        # 11. Decrement level-up timer
        if self._level_up_timer > 0:
            self._level_up_timer -= 1

    # --- Sky blocks (life-restoring blocks) ---

    def _update_sky_blocks(self, speed: float) -> None:
        """Move sky blocks leftward and spawn new ones periodically."""
        for block in self._sky_blocks:
            block.x -= speed * SKY_BLOCK_SPEED_FACTOR
        self._sky_blocks = [b for b in self._sky_blocks if not b.off_screen()]
        self._sky_block_timer -= 1
        if self._sky_block_timer <= 0:
            self._spawn_sky_block()
            self._sky_block_timer = random.randint(*SKY_BLOCK_SPAWN_INTERVAL)

    def _spawn_sky_block(self) -> None:
        """Create a new sky block at the right edge."""
        x = self.width
        y = random.randint(*SKY_BLOCK_HEIGHT_RANGE)
        size = random.randint(*SKY_BLOCK_SIZE_RANGE)
        block = SkyBlock(
            x=x, y=y, size=size,
            color=SKY_BLOCK_COLOR, speed=BASE_SPEED,
        )
        self._sky_blocks.append(block)

    def _check_sky_block_collection(self) -> None:
        """Check if the character collects a sky block (restores a life)."""
        if self._lives >= MAX_LIVES:
            return
        for i, block in enumerate(self._sky_blocks):
            if block.check_collision(self._player.bounding_box):
                block.collected = True
                self._lives = min(self._lives + 1, MAX_LIVES)
                self._sound_manager.play_coin()
                return

    # --- Moving clouds (parallax background) ---

    def _update_clouds(self, speed: float) -> None:
        """Move clouds leftward at a slower speed and spawn new ones."""
        for cloud in self._clouds:
            cloud.x -= speed * CLOUD_SPEED_FACTOR
        self._clouds = [c for c in self._clouds if not c.off_screen()]
        self._cloud_timer -= 1
        if self._cloud_timer <= 0:
            self._spawn_cloud()
            self._cloud_timer = random.randint(*CLOUD_SPAWN_INTERVAL)

    def _spawn_cloud(self) -> None:
        """Create a new cloud at the right edge."""
        width = random.randint(*CLOUD_SIZE_RANGE)
        height = max(width // 2, 20)
        y = random.randint(30, 120)
        cloud = Cloud(
            x=self.width, y=y,
            width=width, height=height,
            color=CLOUD_COLOR, speed=BASE_SPEED,
        )
        self._clouds.append(cloud)

    def render(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render the current game state onto the frame."""
        if self._state == self.MENU:
            self._render_menu(frame)
        elif self._state == self.PLAYING:
            self._render_game(frame, connections)
        elif self._state == self.GAME_OVER:
            self._render_game_over(frame, connections)

    def _render_static_environment(self, frame: np.ndarray) -> None:
        """Draw the Minecraft sky, pixel clouds, and grass-block ground with graffiti."""
        # Sky
        frame[:] = SKY_COLOR

        # Pixel clouds (made of rectangles for a blocky look)
        for cx, cy in _CLOUD_OFFSETS:
            cv2.rectangle(frame, (cx - 30, cy - 8), (cx + 30, cy + 8), CLOUD_COLOR, -1)
            cv2.rectangle(frame, (cx - 50, cy), (cx + 50, cy + 10), CLOUD_COLOR, -1)

        # Grass-block ground
        ground_top = self._ground_y
        ground_height = self.height - ground_top
        grass_h = max(int(ground_height * 0.25), 15)
        dirt_top = ground_top + grass_h

        # Grass top band (green)
        cv2.rectangle(frame, (0, ground_top), (self.width, dirt_top), GRASS_COLOR, -1)
        # Dirt band (brown)
        cv2.rectangle(frame, (0, dirt_top), (self.width, self.height), DIRT_COLOR, -1)
        # Block texture lines
        block_w = 20
        for x in range(0, self.width, block_w):
            cv2.line(frame, (x, ground_top), (x, self.height), MC_BLOCK_BORDER, 1)
        cv2.line(frame, (0, ground_top), (self.width, ground_top), MC_BLOCK_BORDER, 1)
        cv2.line(frame, (0, dirt_top), (self.width, dirt_top), MC_BLOCK_BORDER, 1)

        # Graffiti text on the ground
        text = GRAFFITI_TEXT
        (text_w, text_h), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        text_x = self.width - text_w - 10
        text_y = dirt_top + text_h + 5
        cv2.putText(
            frame, text, (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, GRAFFITI_COLOR, 1, cv2.LINE_AA,
        )

    def _render_game(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render playing game: Minecraft background + character + obstacles + HUD."""
        # Light sky blue background (overridden by static environment)
        frame[:] = (200, 230, 255)
        # Moving clouds (parallax background)
        for cloud in self._clouds:
            cloud.render(frame)
        # Sky blocks (life-restoring blocks)
        for block in self._sky_blocks:
            block.render(frame)
        # Static environment (pixel clouds, bushes, grass-block ground with graffiti)
        self._render_static_environment(frame)
        self._player.render(frame, connections)
        self._obstacle_manager.render(frame)
        self._draw_hud(frame)
        self._render_warning(frame)
        if self._level_up_timer > 0:
            self._render_level_up(frame)

    def _render_warning(self, frame: np.ndarray) -> None:
        """Draw a warning message at the top when the user is too close or far."""
        if self._player.scale_warning:
            cv2.putText(
                frame, "ACERQUE O ALEJE LA CAMARA",
                (self.width // 2 - 120, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, GAME_OVER_COLOR, 2, cv2.LINE_AA,
            )

    def _render_menu(self, frame: np.ndarray) -> None:
        """Render the Minecraft-themed menu screen."""
        frame[:] = SKY_COLOR
        self._render_static_environment(frame)

        # Darken slightly for menu overlay
        overlay = frame.copy()
        overlay[:] = (overlay * 0.5).astype(overlay.dtype)
        frame[:] = overlay

        cx = self.width // 2
        cv2.putText(
            frame, "MINECRAFT MARIO",
            (cx - 110, self.height // 2 - 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, HUD_COLOR, 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame, "Jump to start",
            (cx - 70, self.height // 2 + 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, "Press SPACE to start",
            (cx - 90, self.height // 2 + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

    def _render_game_over(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render game over screen (frozen game frame + overlay)."""
        self._render_game(frame, connections)
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
        (w, h), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        cx = self.width // 2
        cv2.putText(
            frame, text,
            (cx - w // 2, self.height // 2 - 40),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, LEVEL_UP_COLOR, thickness, cv2.LINE_AA,
        )

    def _draw_hearts(self, frame: np.ndarray) -> None:
        """Draw hearts for remaining lives in the top-right corner."""
        for i in range(MAX_LIVES):
            color = HEART_COLOR if i < self._lives else (100, 100, 100)
            cx = self.width - 30 - i * 25
            cy = 25
            cv2.ellipse(
                frame,
                (cx, cy),
                (10, 10),
                0,
                0,
                360,
                color,
                -1,
            )
            cv2.ellipse(
                frame,
                (cx - 7, cy),
                (5, 5),
                0,
                0,
                360,
                color,
                -1,
            )
            cv2.ellipse(
                frame,
                (cx + 7, cy),
                (5, 5),
                0,
                0,
                360,
                color,
                -1,
            )

    def _draw_hud(self, frame: np.ndarray) -> None:
        """Draw score, level, speed, and hearts on the frame."""
        speed_mult = SPEED_MULTIPLIER ** (self._obstacle_manager.level - 1)
        self._draw_hearts(frame)
        cv2.putText(
            frame, f"Bloques: {self.passed_count}",
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
        if key == ord(" "):
            if self._state == self.MENU:
                self.start()
            elif self._state == self.GAME_OVER:
                self.start()
        elif key == ord("q") or key == 27:
            pass  # handled by caller for exit
