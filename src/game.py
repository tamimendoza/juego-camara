"""Endless pose-controlled jumping game module.

Pipeline:
    camera.read_frame → BGR→RGB conversion → mp.Image → PoseLandmarker.detect →
    landmark extraction → GameEngine.update → GameEngine.render → display with OpenCV

The player jumps by physically raising above a baseline (detected from shoulder
landmarks). A miniatura stick-figure character at the bottom of the screen
mirrors the jump and must clear scrolling obstacles. Every 5 obstacles cleared,
the player levels up. Speed increases by 10% starting from level 2. The player
has 3 lives (hearts); each collision with an obstacle costs a life. Sky blocks
in the sky can restore lives. The game ends when all lives are lost.

Audio:
    GroundTheme.mp3 plays as background music during gameplay.
    InvincibilityTheme.mp3 plays when the player has 5+ coins.
    Background music volume is kept below sound effect volume.
"""

import math
import random
import time
from typing import List, Optional, Sequence

import cv2
import numpy as np

from .character import mirror_points
from .silhouette import SilhouetteDrawer
from .sound_manager import SoundManager
from .utils import LandmarkPoint

WINDOW_NAME = "Juego Camara - Mini Juego"
RESOLUTION = (640, 480)

# --- Geometry constants ---
GROUND_Y_RATIO = 0.80
CHARACTER_X = 80
CHARACTER_TARGET_HEIGHT = 90  # pixel height of the miniatura character
HEAD_RADIUS_MIN = 8
TOP_MARGIN = 60.0  # px the character top may not rise above the screen top
MAX_JUMP_OFFSET = max(  # highest jump offset that keeps the character on screen
    GROUND_Y_RATIO * RESOLUTION[1] - CHARACTER_TARGET_HEIGHT - TOP_MARGIN,
    1.0,
)

# --- Jump detection constants ---
JUMP_THRESHOLD = 30.0  # pixels shoulder midpoint must rise above baseline
JUMP_COOLDOWN = 8  # frames between allowed jump triggers
BASELINE_EMA_ALPHA = 0.05  # slow EMA for dynamic baseline adaptation
CROUCH_ANGLE_THRESHOLD = 150.0  # avg knee angle (deg) below which legs are bent
CROUCH_HOLD_FRAMES = 4  # consecutive crouch frames required to arm the jump
ARMED_TIMEOUT_FRAMES = 20  # frames to jump after arming before the arm expires
ANKLE_RISE_THRESHOLD = 10.0  # px ankles must rise to confirm a real jump

# --- Physics constants ---
GRAVITY = 0.6  # px/frame^2
JUMP_VELOCITY = -14.0  # initial upward velocity (px/frame)

# --- Double jump constants ---
MAX_JUMPS = 2
DOUBLE_JUMP_VELOCITY = -10.0

# --- Game speed constants ---
BASE_SPEED = 4.0  # starting obstacle speed (px/frame)
SPEED_MULTIPLIER = 1.10  # multiplied every LEVEL_INTERVAL obstacles
SPEED_INTERVAL = 10  # obstacles passed before speed increases
LEVEL_INTERVAL = 5  # obstacles passed before level increments

# --- Lives system constants ---
MAX_LIVES = 3
HEART_COLOR = (0, 0, 255)  # red hearts (BGR)

# --- Sky block constants ---
SKY_BLOCK_SIZE = 30
SKY_BLOCK_COLOR = (0, 255, 255)  # yellow (BGR)
SKY_BLOCK_SPEED_FACTOR = 0.5  # sky blocks move at 50% of obstacle speed
SKY_BLOCK_SPAWN_INTERVAL = (120, 240)  # frames between sky block spawns
SKY_BLOCK_HEIGHT_RANGE = (80, 200)  # y positions for sky blocks
SKY_BLOCK_SIZE_RANGE = (20, 40)  # sky block sizes

# --- Cloud constants ---
CLOUD_COLOR = (255, 255, 255)  # white
CLOUD_SPEED_FACTOR = 0.3  # clouds move at 30% of obstacle speed
CLOUD_SPAWN_INTERVAL = (180, 300)  # frames between cloud spawns
CLOUD_SIZE_RANGE = (40, 80)  # cloud sizes

# --- Ground constants ---
BRICK_COLOR = (0, 128, 255)  # orange-red bricks (BGR)
GRAFFITI_TEXT = "Familia Mendoza Silva"
GRAFFITI_COLOR = (255, 255, 255)  # white graffiti

# --- Pose stability constants ---
POSE_WARNING_TEXT = "Acerquese o alejese de la camara"
POSE_WARNING_COLOR = (0, 0, 255)  # red warning text
MIN_SHOULDER_WIDTH = 30
MAX_SHOULDER_WIDTH = 400

# --- Invincibility constants ---
INVINCIBILITY_THRESHOLD = 5  # score at which invincibility theme plays

# --- Obstacle constants ---
OBSTACLE_WIDTH = 30
OBSTACLE_HEIGHT_RANGE = (50, 120)  # random obstacle heights
OBSTACLE_GAP_RANGE = (40, 90)  # random frames between spawns

# --- Rendering colors (BGR) ---
OBSTACLE_COLOR = (0, 100, 255)  # orange-red
HUD_COLOR = (255, 255, 255)  # white

# --- Landmark indices ---
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


class JumpDetector:
    """Detects a physical jump from pose landmarks using a two-phase gesture.

    A jump only fires when the player first bends their legs (crouches — the
    average knee angle drops below ``CROUCH_ANGLE_THRESHOLD`` for
    ``CROUCH_HOLD_FRAMES`` frames, arming the detector) and then performs an
    actual jump — the whole body (shoulders AND ankles) rises above the crouch
    baseline. Raising the shoulders alone never triggers a jump, and crouching
    without a takeoff never fires (the arm expires after
    ``ARMED_TIMEOUT_FRAMES``).

    States:
      IDLE       — EMA shoulder baseline adapts; arms when the legs stay bent.
      ARMED      — legs are bent; fires when shoulders AND ankles rise.
      cooldown   — blocks further triggers for a few frames after a jump fires.
    """

    def __init__(
        self,
        threshold: float = JUMP_THRESHOLD,
        cooldown: int = JUMP_COOLDOWN,
        ema_alpha: float = BASELINE_EMA_ALPHA,
    ):
        self._threshold = threshold
        self._cooldown = cooldown
        self._ema_alpha = ema_alpha
        self._baseline_y: Optional[float] = None
        self._cooldown_counter = 0
        self._frame_count = 0

        # Two-phase (crouch → jump) state
        self._crouch_frames = 0
        self._armed = False
        self._armed_frames = 0
        self._crouch_baseline: Optional[float] = None
        self._ankle_baseline: Optional[float] = None

    def update(self, landmarks: Sequence[LandmarkPoint]) -> bool:
        """Process a frame of landmarks. Returns True if a jump should fire."""
        if not self._has_shoulders(landmarks):
            self._frame_count += 1
            self._crouch_frames = 0
            return False

        shoulder_y = self._shoulder_midpoint_y(landmarks)

        # In cooldown: count down, no jump trigger
        if self._cooldown_counter > 0:
            self._cooldown_counter -= 1
            self._frame_count += 1
            self._crouch_frames = 0
            return False

        if self._armed:
            self._armed_frames += 1
            if self._armed_frames > ARMED_TIMEOUT_FRAMES:
                self._disarm()
            else:
                ankle_y = self._ankle_midpoint_y(landmarks)
                if (
                    ankle_y is not None
                    and self._crouch_baseline is not None
                    and self._ankle_baseline is not None
                    and shoulder_y < self._crouch_baseline - self._threshold
                    and ankle_y < self._ankle_baseline - ANKLE_RISE_THRESHOLD
                ):
                    self._disarm()
                    self._cooldown_counter = self._cooldown
                    self._frame_count += 1
                    return True
        else:
            # IDLE: slowly adapt baseline to gradual position changes
            if self._baseline_y is None:
                self._baseline_y = shoulder_y
            else:
                self._baseline_y = (
                    self._baseline_y * (1 - self._ema_alpha)
                    + shoulder_y * self._ema_alpha
                )

            # Arm the jump when the legs stay bent
            if self._is_crouched(landmarks):
                self._crouch_frames += 1
                if self._crouch_frames >= CROUCH_HOLD_FRAMES:
                    self._crouch_baseline = shoulder_y
                    ankle_baseline = self._ankle_midpoint_y(landmarks)
                    self._ankle_baseline = (
                        ankle_baseline if ankle_baseline is not None else shoulder_y
                    )
                    self._armed = True
                    self._armed_frames = 0
                    self._crouch_frames = 0
            else:
                self._crouch_frames = 0

        self._frame_count += 1
        return False

    def _disarm(self) -> None:
        """Clear the armed state back to IDLE."""
        self._armed = False
        self._armed_frames = 0
        self._crouch_frames = 0
        self._crouch_baseline = None
        self._ankle_baseline = None

    @staticmethod
    def _has_shoulders(landmarks: Sequence[LandmarkPoint]) -> bool:
        """Check that both shoulder landmarks are visible."""
        return (
            len(landmarks) > RIGHT_SHOULDER
            and landmarks[LEFT_SHOULDER] is not None
            and landmarks[RIGHT_SHOULDER] is not None
        )

    @staticmethod
    def _shoulder_midpoint_y(landmarks: Sequence[LandmarkPoint]) -> float:
        """Return the average y of left and right shoulder landmarks."""
        ls = landmarks[LEFT_SHOULDER]
        rs = landmarks[RIGHT_SHOULDER]
        return (ls[1] + rs[1]) / 2.0

    @staticmethod
    def _ankle_midpoint_y(landmarks: Sequence[LandmarkPoint]) -> Optional[float]:
        """Return the average y of left and right ankle landmarks, or None."""
        if len(landmarks) <= RIGHT_ANKLE:
            return None
        la = landmarks[LEFT_ANKLE]
        ra = landmarks[RIGHT_ANKLE]
        if la is None or ra is None:
            return None
        return (la[1] + ra[1]) / 2.0

    @staticmethod
    def _knee_angle(
        hip: LandmarkPoint,
        knee: LandmarkPoint,
        ankle: LandmarkPoint,
    ) -> Optional[float]:
        """Return the angle (degrees) at the knee joint, or None if degenerate."""
        if hip is None or knee is None or ankle is None:
            return None
        v1 = (hip[0] - knee[0], hip[1] - knee[1])
        v2 = (ankle[0] - knee[0], ankle[1] - knee[1])
        n1 = math.hypot(v1[0], v1[1])
        n2 = math.hypot(v2[0], v2[1])
        if n1 < 1e-6 or n2 < 1e-6:
            return None
        cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
        return math.degrees(math.acos(cos))

    @classmethod
    def _is_crouched(cls, landmarks: Sequence[LandmarkPoint]) -> bool:
        """True when both knees are bent below CROUCH_ANGLE_THRESHOLD."""
        if len(landmarks) <= RIGHT_ANKLE:
            return False
        left = cls._knee_angle(
            landmarks[LEFT_HIP],
            landmarks[LEFT_KNEE],
            landmarks[LEFT_ANKLE],
        )
        right = cls._knee_angle(
            landmarks[RIGHT_HIP],
            landmarks[RIGHT_KNEE],
            landmarks[RIGHT_ANKLE],
        )
        if left is None or right is None:
            return False
        return (left + right) / 2.0 < CROUCH_ANGLE_THRESHOLD

    def reset(self) -> None:
        """Clear the baseline, cooldown, and two-phase state on game restart."""
        self._baseline_y = None
        self._cooldown_counter = 0
        self._frame_count = 0
        self._disarm()


class PlayerCharacter:
    """A small stick-figure character ("miniatura") with jump physics.

    Positioned at a fixed x near the bottom of the screen. Pose landmarks are
    scaled and translated to render a miniaturized version of the player's
    pose. Jump physics (velocity + gravity) move the character vertically.
    """

    def __init__(
        self,
        x: int,
        ground_y: int,
        scale: float = 0.30,
        color: tuple = (0, 0, 255),  # red BGR
    ):
        self.x = x
        self.ground_y = ground_y
        self._scale = scale
        self._color = color

        self._vy = 0.0
        self._on_ground = True
        self._jump_offset = 0.0  # pixels above ground_y
        self._jump_count = 0

        self._drawer = SilhouetteDrawer()
        self._drawer.line_color = color
        self._drawer.joint_color = color
        self._drawer.silhouette_color = color
        self._drawer.line_thickness = 1
        self._drawer.joint_radius = 3

        # Latest transformed pose points for rendering
        self._render_points: Optional[List[LandmarkPoint]] = None
        # Bounding box for collision (recomputed in _update_transform)
        self._bbox: tuple = (0, 0, 0, 0)
        # Pose stability warning (user too close/far or shoulders not detected)
        self.scale_warning = False

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

    def _update_render_points(
        self, landmarks: Sequence[LandmarkPoint]
    ) -> None:
        """Scale and translate pose landmarks to miniatura position.

        Centers the pose on its shoulder midpoint (or centroid if shoulders
        are occluded), scales to ``CHARACTER_TARGET_HEIGHT`` pixels tall, and
        positions the character so its bottom rests on the ground line
        (offset upward by ``_jump_offset`` when jumping).
        """
        points = list(landmarks)

        # Visible points for height / fallback center
        visible = [p for p in points if p is not None]
        if len(visible) < 3:
            self._render_points = None
            self._bbox = (0, 0, 0, 0)
            return

        # Center: shoulder midpoint if both visible, else centroid
        ls = points[LEFT_SHOULDER] if len(points) > LEFT_SHOULDER else None
        rs = points[RIGHT_SHOULDER] if len(points) > RIGHT_SHOULDER else None
        if ls is not None and rs is not None:
            cx = (ls[0] + rs[0]) / 2.0
            cy = (ls[1] + rs[1]) / 2.0
        else:
            cx = sum(p[0] for p in visible) / len(visible)
            cy = sum(p[1] for p in visible) / len(visible)

        # Full pose height (topmost to bottommost visible landmark)
        all_y = [p[1] for p in visible]
        min_y_vis = min(all_y)
        max_y_vis = max(all_y)
        pose_height = max_y_vis - min_y_vis
        if pose_height < 10:
            pose_height = 10.0

        scale = CHARACTER_TARGET_HEIGHT / pose_height

        # Position so the bottom of the pose (max_y_vis) lands at ground_y
        # + jump_offset.  When jump_offset=0, the character's feet are at the
        # ground line.
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

        # Bounding box with padding for collision detection
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
        """Draw the miniatura on the frame as head circle + body lines."""
        if self._render_points is None:
            # Fallback: simple static stick figure
            self._draw_fallback(frame)
            return

        styles = ["head_circle", "body_lines", "torso_fill"]
        self._drawer.render_character(
            frame,
            self._render_points,
            connections=list(connections) if connections else None,
            styles=styles,
        )

    def _draw_fallback(self, frame: np.ndarray) -> None:
        """Draw a simple static stick figure when no pose is available."""
        cx = self.x
        cy = int(self.ground_y + self._jump_offset)
        r = HEAD_RADIUS_MIN
        cv2.circle(frame, (cx, cy - r), r, self._color, -1)
        # Body line
        cv2.line(frame, (cx, cy), (cx, cy + 30), self._drawer.line_color, 2)


class Obstacle:
    """A rectangular obstacle moving leftward at the current game speed."""

    def __init__(
        self,
        x: int,
        ground_y: int,
        width: int = OBSTACLE_WIDTH,
        height: int = OBSTACLE_HEIGHT_RANGE[0],
        speed: float = BASE_SPEED,
        color: tuple = OBSTACLE_COLOR,
    ):
        self.x = float(x)
        self.ground_y = ground_y
        self.width = width
        self.height = height
        self.speed = speed
        self.color = color
        self.passed = False

    def update(self) -> None:
        """Move leftward by the current speed."""
        self.x -= self.speed

    def render(self, frame: np.ndarray) -> None:
        """Draw the obstacle as a filled rectangle on the ground."""
        x0 = int(self.x)
        x1 = int(self.x + self.width)
        y0 = self.ground_y - self.height
        y1 = self.ground_y
        cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 0, 0), 2)

    def off_screen(self) -> bool:
        """Check if the obstacle has moved completely off the left edge."""
        return self.x + self.width < 0

    def check_collision(self, bbox: tuple) -> bool:
        """AABB collision check. bbox = (x, y, w, h).

        Returns ``False`` once the obstacle has been marked as passed (the
        point / coin sound has already been scored), preventing the character
        from colliding with an obstacle that has already cleared them.
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


class SkyBlock:
    """A square block in the sky that grants a life when touched by the character.

    Moves leftward at cloud speed (slower than obstacles for parallax effect).
    Disappears after being collected (plays coin sound, grants +1 life).
    """

    def __init__(
        self,
        x: int,
        y: int,
        size: int = SKY_BLOCK_SIZE,
        color: tuple = SKY_BLOCK_COLOR,
        speed: float = BASE_SPEED,
        sprite: Optional[np.ndarray] = None,
    ):
        self.x = float(x)
        self.y = y
        self.size = size
        self.color = color
        self.speed = speed * CLOUD_SPEED_FACTOR
        self.collected = False
        self.sprite = sprite

    def update(self) -> None:
        """Move leftward at cloud speed."""
        self.x -= self.speed

    def render(self, frame: np.ndarray) -> None:
        """Draw the sky block using its sprite, or as a filled square."""
        if self.sprite is not None:
            sprite = cv2.resize(self.sprite, (self.size, self.size))
            self._blend_sprite(frame, sprite)
            return
        x0 = int(self.x)
        y0 = int(self.y)
        x1 = int(self.x + self.size)
        y1 = int(self.y + self.size)
        cv2.rectangle(frame, (x0, y0), (x1, y1), self.color, -1)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 0, 0), 2)

    def _blend_sprite(self, frame: np.ndarray, sprite: np.ndarray) -> None:
        """Alpha-blend a BGRA sprite over the frame at the block's position."""
        x0 = max(int(self.x), 0)
        y0 = max(int(self.y), 0)
        x1 = min(int(self.x) + self.size, frame.shape[1])
        y1 = min(int(self.y) + self.size, frame.shape[0])
        if x0 >= x1 or y0 >= y1:
            return
        sx = x0 - int(self.x)
        sy = y0 - int(self.y)
        spr = sprite[sy:sy + (y1 - y0), sx:sx + (x1 - x0)]
        bgr = spr[:, :, :3].astype(np.float32)
        alpha = (spr[:, :, 3].astype(np.float32) / 255.0)[..., np.newaxis]
        region = frame[y0:y1, x0:x1].astype(np.float32)
        frame[y0:y1, x0:x1] = (bgr * alpha + region * (1 - alpha)).astype(np.uint8)

    def off_screen(self) -> bool:
        """Check if the sky block has moved completely off the left edge."""
        return self.x + self.size < 0

    def check_collision(self, bbox: tuple) -> bool:
        """AABB collision check. bbox = (x, y, w, h)."""
        if self.collected:
            return False
        block_bbox = (self.x, self.y, self.size, self.size)
        return self._aabb_overlap(block_bbox, bbox)

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


class Cloud:
    """A cloud that moves leftward at a slower speed than obstacles (parallax)."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple = CLOUD_COLOR,
        speed: float = BASE_SPEED,
        sprite: Optional[np.ndarray] = None,
    ):
        self.x = float(x)
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.speed = speed * CLOUD_SPEED_FACTOR
        self.sprite = sprite

    def update(self) -> None:
        """Move leftward at cloud speed."""
        self.x -= self.speed

    def render(self, frame: np.ndarray) -> None:
        """Draw the cloud using its sprite, or as an ellipse when no sprite."""
        if self.sprite is not None:
            sprite = cv2.resize(self.sprite, (self.width, self.height))
            self._blend_sprite(frame, sprite)
            return
        cx = int(self.x + self.width / 2)
        cy = int(self.y + self.height / 2)
        cv2.ellipse(
            frame,
            (cx, cy),
            (self.width // 2, self.height // 2),
            0,
            0,
            360,
            self.color,
            -1,
        )

    def _blend_sprite(self, frame: np.ndarray, sprite: np.ndarray) -> None:
        """Alpha-blend a BGRA sprite over the frame at the cloud's position."""
        x0 = max(int(self.x), 0)
        y0 = max(int(self.y), 0)
        x1 = min(int(self.x) + self.width, frame.shape[1])
        y1 = min(int(self.y) + self.height, frame.shape[0])
        if x0 >= x1 or y0 >= y1:
            return
        sx = x0 - int(self.x)
        sy = y0 - int(self.y)
        spr = sprite[sy:sy + (y1 - y0), sx:sx + (x1 - x0)]
        bgr = spr[:, :, :3].astype(np.float32)
        alpha = (spr[:, :, 3].astype(np.float32) / 255.0)[..., np.newaxis]
        region = frame[y0:y1, x0:x1].astype(np.float32)
        frame[y0:y1, x0:x1] = (bgr * alpha + region * (1 - alpha)).astype(np.uint8)

    def off_screen(self) -> bool:
        """Check if the cloud has moved completely off the left edge."""
        return self.x + self.width < 0


class ObstacleManager:
    """Spawns and manages obstacles, tracks score, and controls speed."""

    def __init__(
        self,
        width: int,
        ground_y: int,
        base_speed: float = BASE_SPEED,
        spawn_interval_range: tuple = OBSTACLE_GAP_RANGE,
    ):
        self.width = width
        self.ground_y = ground_y
        self._spawn_interval_range = spawn_interval_range
        self._speed = base_speed
        self._obstacles: List[Obstacle] = []
        self._spawn_timer = 0
        self._passed_count = 0

    @property
    def passed_count(self) -> int:
        return self._passed_count

    @property
    def level(self) -> int:
        """Current level: increments every LEVEL_INTERVAL obstacles passed."""
        return self._passed_count // LEVEL_INTERVAL + 1

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
        # Update existing obstacles
        for obs in self._obstacles:
            obs.update()

        # Check passing and remove off-screen
        new_obstacles = []
        for obs in self._obstacles:
            if not obs.passed and obs.mark_passed(character_x):
                self._passed_count += 1
            if not obs.off_screen():
                new_obstacles.append(obs)
        self._obstacles = new_obstacles

        # Spawn new obstacles
        self._spawn_timer -= 1
        if self._spawn_timer <= 0:
            self._spawn()
            self._spawn_timer = random.randint(*self._spawn_interval_range)

    def _spawn(self) -> None:
        """Create a new obstacle at the right edge."""
        height = random.randint(*OBSTACLE_HEIGHT_RANGE)
        obs = Obstacle(
            x=self.width,
            ground_y=self.ground_y,
            width=OBSTACLE_WIDTH,
            height=height,
            speed=self._speed,
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


class GameEngine:
    """Manages game state, scoring, speed progression, and rendering.

    States:
        MENU (0) → PLAYING (1) → GAME_OVER (2)
    """

    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

    def __init__(self, width: int, height: int, sound_manager: Optional[SoundManager] = None):
        self.width = width
        self.height = height
        self._ground_y = int(height * GROUND_Y_RATIO)

        self._player = PlayerCharacter(CHARACTER_X, self._ground_y)
        self._obstacle_manager = ObstacleManager(width, self._ground_y)
        self._jump_detector = JumpDetector()
        self._sound_manager = sound_manager if sound_manager is not None else SoundManager()

        self._state = self.MENU
        self._frame_count = 0

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
    def lives(self) -> int:
        """Current number of lives remaining (0 to MAX_LIVES)."""
        return self._lives

    @property
    def level(self) -> int:
        """Current level: increments every LEVEL_INTERVAL obstacles passed."""
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

        # 5. Update obstacles
        old_passed = self._obstacle_manager.passed_count
        self._obstacle_manager.update(
            CHARACTER_X, self._player.bounding_box
        )
        if self._obstacle_manager.passed_count > old_passed:
            self._sound_manager.play_coin()

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

    def render(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render the current game state onto the frame."""
        if self._state == self.MENU:
            self._render_menu(frame)
        elif self._state == self.PLAYING:
            self._render_game(frame, connections)
        elif self._state == self.GAME_OVER:
            self._render_game_over(frame, connections)

    def _update_sky_blocks(self, current_speed: float) -> None:
        """Update sky blocks: move, check collisions, spawn new ones."""
        # Update existing sky blocks
        for block in self._sky_blocks:
            block.update()

        # Check collisions with character
        char_bbox = self._player.bounding_box
        for block in self._sky_blocks:
            if not block.collected and block.check_collision(char_bbox):
                if self._lives < MAX_LIVES:
                    self._lives += 1
                    self._sound_manager.play_coin()
                block.collected = True

        # Remove off-screen and collected blocks
        self._sky_blocks = [
            b for b in self._sky_blocks
            if not b.off_screen() and not b.collected
        ]

        # Spawn new sky blocks
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
        # Update existing clouds
        for cloud in self._clouds:
            cloud.update()

        # Remove off-screen clouds
        self._clouds = [c for c in self._clouds if not c.off_screen()]

        # Spawn new clouds
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

    def _render_game(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render playing game: sky background + clouds + character + obstacles + ground + HUD."""
        # Sky blue background (de-identified, no camera feed)
        frame[:] = (200, 230, 255)  # light sky blue (BGR)

        # Render clouds (behind everything)
        for cloud in self._clouds:
            cloud.render(frame)

        # Render sky blocks
        for block in self._sky_blocks:
            block.render(frame)

        # Draw brick ground
        self._draw_brick_ground(frame)

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

    def _render_menu(self, frame: np.ndarray) -> None:
        """Render the menu screen."""
        frame[:] = 0
        cv2.putText(
            frame,
            "POSE JUMP GAME",
            (self.width // 2 - 120, self.height // 2 - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            HUD_COLOR,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Jump to start",
            (self.width // 2 - 80, self.height // 2 + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Press SPACE to start",
            (self.width // 2 - 100, self.height // 2 + 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )

    def _render_game_over(self, frame: np.ndarray, connections: Sequence[tuple]) -> None:
        """Render game over screen (frozen game frame + overlay)."""
        self._render_game(frame, connections)
        # Dim the game slightly
        frame[:] = (frame * 0.4).astype(frame.dtype)

        speed_mult = SPEED_MULTIPLIER ** (self.level - 1)

        cv2.putText(
            frame,
            "GAME OVER",
            (self.width // 2 - 80, self.height // 2 - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Score: {self.passed_count}",
            (self.width // 2 - 40, self.height // 2 + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            HUD_COLOR,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Level: {self.level}",
            (self.width // 2 - 40, self.height // 2 + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Speed: {speed_mult:.1f}x",
            (self.width // 2 - 40, self.height // 2 + 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Press SPACE to restart",
            (self.width // 2 - 90, self.height // 2 + 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )

    def _draw_brick_ground(self, frame: np.ndarray) -> None:
        """Draw a brick-colored ground strip with graffiti text."""
        ground_height = self.height - self._ground_y
        cv2.rectangle(
            frame,
            (0, self._ground_y),
            (self.width, self.height),
            BRICK_COLOR,
            -1,
        )
        # Brick pattern lines
        for y in range(self._ground_y, self.height, 10):
            cv2.line(frame, (0, y), (self.width, y), (0, 60, 130), 1)
        for x in range(0, self.width, 20):
            cv2.line(
                frame,
                (x, self._ground_y),
                (x, self.height),
                (0, 60, 130),
                1,
            )
        # Graffiti text
        cv2.putText(
            frame,
            GRAFFITI_TEXT,
            (self.width // 2 - 100, self._ground_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            GRAFFITI_COLOR,
            1,
            cv2.LINE_AA,
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
        """Draw level, score, speed multiplier, and hearts on the frame."""
        speed_mult = SPEED_MULTIPLIER ** (self.level - 1)
        self._draw_hearts(frame)
        cv2.putText(
            frame,
            f"Level: {self.level}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            HUD_COLOR,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Obstacles: {self.passed_count}",
            (10, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Speed: {speed_mult:.1f}x",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )

    def handle_key(self, key: int) -> None:
        """Handle keyboard input for game control."""
        if key == ord(" "):  # SPACE
            if self._state == self.MENU:
                self.start()
            elif self._state == self.GAME_OVER:
                self.start()
        elif key == ord("q") or key == 27:  # q or ESC
            pass  # handled by caller for exit
