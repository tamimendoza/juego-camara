"""Mario Bros game variant with real face overlay.

Pipeline:
    camera.read_frame -> BGR->RGB conversion -> mp.Image -> PoseLandmarker.detect ->
    FaceLandmarker.detect -> FaceCropper.crop_face -> landmark extraction ->
    MarioFaceGameEngine.update -> MarioFaceGameEngine.render -> display

This variant replaces the Mario character's head (peach face circle + red cap +
brown hair arc) with the person's real face, cropped from the camera feed using
MediaPipe FaceLandmarker (Tasks API, ``face_landmarker.task``).  The Mario body
(red shirt + blue overalls) and all game mechanics (jump physics, obstacles,
levels, lives, sound) are reused from the base Mario game.

Usage:
    python3 -m src.games.mario
    # or: ./run_mario_face.sh
"""

import os
import random
from typing import Optional

import cv2
import numpy as np

from ...core.face_landmarker import FaceLandmarkerDetector
from ...core.face_crop import FaceCropper
from .mario_game import (
    BASE_SPEED,
    MarioCharacter,
    MarioGameEngine,
    RESOLUTION,
    WINDOW_NAME,
    SKY_COLOR,
    HUD_COLOR,
    SKY_BLOCK_SIZE,
    SKY_BLOCK_COLOR,
    SKY_BLOCK_HEIGHT_RANGE,
    MAX_LIVES,
    CLOUD_COLOR,
    CLOUD_SIZE_RANGE,
    SkyBlock,
    Cloud,
    POSE_WARNING_TEXT,
    POSE_WARNING_COLOR,
)

# --- Face Jump speed rules ---
SPEED_INCREMENT = 0.1  # additive speed multiplier increase per level

# --- Graffiti placement ---
GRAFFITI_BRICK_Y_OFFSET = 15  # pixels below ground_y for the graffiti baseline

# Face variant runs at a higher camera resolution so a distant face keeps enough
# pixels for FaceLandmarker to detect and track it reliably.
FACE_RESOLUTION = (1280, 720)


def _resource_path(*parts: str) -> str:
    """Resolve a path under the repo's ``sprites/`` directory.

    The module lives at ``src/games/mario/`` so the repo root is three levels
    up; sprites are always resolved from the repository root regardless of the
    current working directory.
    """
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    return os.path.join(repo_root, "sprites", *parts)


def _load_sprite(*parts: str) -> Optional[np.ndarray]:
    """Load a BGRA sprite with ``IMREAD_UNCHANGED``; return None on any failure."""
    try:
        img = cv2.imread(_resource_path(*parts), cv2.IMREAD_UNCHANGED)
    except Exception:
        return None
    if img is None or img.ndim != 3 or img.shape[2] != 4:
        return None
    return img


_CLOUD_SPRITE = _load_sprite("cloud_sprite.png")
_SKY_BLOCK_SPRITE = _load_sprite("SMW_v-ram-yane_QuestionMarkBlock.png")


class DrawnCloud(Cloud):
    """A cloud drawn with overlapping puffy ellipses instead of a sprite.

    Renders a wide, flat cloud with a row of rounded bumps on top so it reads
    as a cloud rather than a flame. Movement and off-screen logic are inherited
    from ``Cloud``.
    """

    def render(self, frame: np.ndarray) -> None:
        x0 = int(self.x)
        y0 = int(self.y)
        w = int(self.width)
        h = int(self.height)
        cx = x0 + w // 2
        bottom = y0 + h
        r = max(h // 2, 3)

        # Flat base band
        cv2.rectangle(
            frame, (x0, bottom - r), (x0 + w, bottom), self.color, -1,
        )
        # Rounded bumps on top of the base
        bump_y = bottom - r
        cv2.circle(frame, (cx - w // 4, bump_y), r, self.color, -1)
        cv2.circle(frame, (cx, bump_y - r // 3), r, self.color, -1)
        cv2.circle(frame, (cx + w // 4, bump_y), r, self.color, -1)


class MarioFaceCharacter(MarioCharacter):
    """Mario character variant with the head replaced by a real face crop.

    Instead of drawing a peach face circle + red cap + brown hair arc, this
    variant overlays the person's real face (cropped from the camera feed)
    at the nose position.  The Mario body (red shirt + blue overalls) is
    rendered identically to the base variant.

    When no face crop is available (FaceMesh didn't detect a face), the
    character falls back to the standard Mario head rendering.
    """

    def render(
        self,
        frame: np.ndarray,
        connections: list,
        face_image: np.ndarray = None,
        face_mask: np.ndarray = None,
    ) -> None:
        """Render the character with a real face overlay instead of a Mario head.

        Args:
            frame: The display canvas (solid background, no camera feed).
            connections: Pose landmark connections for body skeleton.
            face_image: Cropped face region from the camera frame (BGR).
            face_mask: Circular alpha mask for the face crop (single channel).
        """
        if self._render_points is None:
            self._draw_fallback(frame)
            return

        if face_image is not None and face_mask is not None:
            styles = ["mario_body", "face_overlay", "torso_fill"]
        else:
            styles = ["mario_head", "mario_body", "torso_fill"]

        self._drawer.render_character(
            frame,
            self._render_points,
            mask_binary=None,
            connections=connections,
            styles=styles,
            face_image=face_image,
            face_mask=face_mask,
        )


class MarioFaceGameEngine(MarioGameEngine):
    """Mario Bros game engine variant with real face overlay.

    Extends the base Mario game engine by adding MediaPipe FaceLandmarker detection
    (Tasks API with ``face_landmarker.task``) and face cropping.  The person's
    face is cropped from the camera frame and overlaid on the Mario
    character's head position, replacing the peach face circle + cap + hair
    arc.

    Args:
        width: Display width in pixels.
        height: Display height in pixels.
        sound_manager: Sound manager instance.
        face_landmarker: FaceLandmarkerDetector instance (Tasks API wrapper).
        face_cropper: FaceCropper instance.
    """

    _FACE_CROP_RADIUS = 40
    _FACE_PREVIEW_RADIUS = 25
    _FACE_HOLD_FRAMES = 5  # keep the last valid crop across brief detection losses

    def __init__(
        self,
        width: int,
        height: int,
        sound_manager,
        face_landmarker: FaceLandmarkerDetector,
        face_cropper: FaceCropper,
        score_store=None,
    ):
        super().__init__(width, height, sound_manager, score_store=score_store)
        self._player = MarioFaceCharacter(
            self._player.x, self._player.ground_y,
        )
        self._face_landmarker = face_landmarker
        self._face_cropper = face_cropper
        self._face_image: np.ndarray = None
        self._face_mask: np.ndarray = None
        self._face_hold_count = 0  # consecutive frames holding a stale crop
        self._sky_block_spawn_level = 1  # level at which the last sky block spawned
        self._state = self.NAME_ENTRY

    @property
    def speed(self) -> float:
        """Additive speed multiplier: ``BASE_SPEED * (1 + 0.1 * (level - 1))``."""
        return BASE_SPEED * (1 + SPEED_INCREMENT * (self._obstacle_manager.level - 1))

    def handle_key(self, key: int) -> None:
        """Handle keyboard input for the Face variant.

        ENTER from GAME_OVER returns to the name-entry screen instead of
        restarting directly; all other keys delegate to the base engine.
        """
        if self._state == self.GAME_OVER and key in (13, 10):
            self.reset()
            return
        super().handle_key(key)

    def detect_face(self, rgb_frame: np.ndarray, bgr_frame: np.ndarray) -> None:
        """Run FaceLandmarker detection and crop the face from the camera frame.

        Keeps the last valid crop for up to ``_FACE_HOLD_FRAMES`` consecutive
        frames when detection briefly fails, so the face does not flicker.

        Args:
            rgb_frame: RGB frame from the camera (height x width x 3).
            bgr_frame: BGR frame from the camera (for face cropping).
        """
        face_landmarks, face_bbox = self._face_landmarker.detect(rgb_frame)
        if face_landmarks is not None:
            self._face_image, self._face_mask = self._face_cropper.crop_face(
                bgr_frame,
                face_landmarks,
                self.width,
                self.height,
                self._FACE_CROP_RADIUS,
                face_bbox=face_bbox,
            )
            self._face_hold_count = 0
        elif self._face_hold_count < self._FACE_HOLD_FRAMES:
            self._face_hold_count += 1
        else:
            self._face_image = None
            self._face_mask = None
            self._face_hold_count = 0

    def update(
        self,
        points: list,
        connections: list,
        bgr_frame: Optional[np.ndarray] = None,
    ) -> None:
        """Update game state with pose landmarks.

        Args:
            points: Landmark pixel points (list of LandmarkPoint).
            connections: Pose landmark connections.
            bgr_frame: Current BGR frame from the camera (unused; face crop
                is handled separately by ``detect_face``).
        """
        super().update(points, connections)

    def reset(self) -> None:
        """Reset game state, the sky block spawn milestone, and the name buffer.

        The Face variant returns to the NAME_ENTRY state (instead of MENU) with
        an empty name buffer, so the player is prompted before the next game.
        """
        super().reset()
        self._sky_block_spawn_level = 1
        self._state = self.NAME_ENTRY
        self._player_name = ""

    def _render_game(self, frame: np.ndarray, connections: list) -> None:
        """Render the playing game state with face overlay on the character.

        Mirrors the parent's ``_render_game`` but passes the face crop to the
        player's render method for the face overlay.
        """
        frame[:] = SKY_COLOR

        for cloud in self._clouds:
            cloud.render(frame)

        for block in self._sky_blocks:
            block.render(frame)

        self._render_static_environment(
            frame, draw_clouds=False,
            graffiti_y=self._ground_y + GRAFFITI_BRICK_Y_OFFSET,
        )

        self._obstacle_manager.render(frame)

        self._player.render(
            frame,
            connections,
            face_image=self._face_image,
            face_mask=self._face_mask,
        )

        self._draw_hud(frame)

        self._draw_face_preview(frame)

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

        if self._level_up_timer > 0:
            self._render_level_up(frame)

    def _render_menu(self, frame: np.ndarray) -> None:
        """Render the Mario Face Jump menu screen."""
        frame[:] = SKY_COLOR
        self._render_static_environment(
            frame,
            graffiti_y=self._ground_y + GRAFFITI_BRICK_Y_OFFSET,
        )

        overlay = frame.copy()
        overlay[:] = (overlay * 0.5).astype(overlay.dtype)
        frame[:] = overlay

        cx = self.width // 2
        cv2.putText(
            frame, "MARIO FACE JUMP",
            (cx - 120, self.height // 2 - 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, HUD_COLOR, 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Press SPACE to start",
            (cx - 100, self.height // 2 + 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

    def _render_name_entry(self, frame: np.ndarray) -> None:
        """Render the name-entry screen with the name being typed."""
        frame[:] = SKY_COLOR
        self._render_static_environment(
            frame,
            graffiti_y=self._ground_y + GRAFFITI_BRICK_Y_OFFSET,
        )

        overlay = frame.copy()
        overlay[:] = (overlay * 0.5).astype(overlay.dtype)
        frame[:] = overlay

        cx = self.width // 2
        cv2.putText(
            frame, "MARIO FACE JUMP",
            (cx - 120, self.height // 2 - 80),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, HUD_COLOR, 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame, "Enter your name:",
            (cx - 90, self.height // 2 - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUD_COLOR, 1, cv2.LINE_AA,
        )
        name_text = self._player_name + "_"
        cv2.putText(
            frame, name_text,
            (cx - 90, self.height // 2 + 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame, "Press ENTER to start",
            (cx - 100, self.height // 2 + 80),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

    def _draw_face_preview(self, frame: np.ndarray) -> None:
        """Draw a small live face preview circle on the bricks at the lower right.

        Uses the same ``face_image`` / ``face_mask`` as the character's head so
        the player can verify the face fits and is centered in the head circle
        when standing far from the camera. When no face is detected, only the
        circle outline is drawn.
        """
        center = (self.width - 35, self._ground_y + 30)
        radius = self._FACE_PREVIEW_RADIUS

        if self._face_image is not None and self._face_mask is not None:
            FaceCropper().overlay_face(
                frame, self._face_image, self._face_mask, center, radius,
            )
        else:
            cv2.circle(frame, center, radius, HUD_COLOR, 1, cv2.LINE_AA)

    def _update_sky_blocks(self, current_speed: float) -> None:
        """Update sky blocks: move, restore a life on collect, spawn one per level up.

        Collecting a sky block restores +1 life (heart) up to ``MAX_LIVES``,
        matching the base engine; a single block spawns each time the level
        rises (every 5 obstacles passed) instead of on a random timer.
        """
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

        if self.level > self._sky_block_spawn_level:
            self._sky_block_spawn_level = self.level
            self._spawn_sky_block(current_speed)

    def _spawn_sky_block(self, current_speed: float) -> None:
        """Create a sky block at the right edge using the question-mark sprite."""
        y = random.randint(*SKY_BLOCK_HEIGHT_RANGE)
        block = SkyBlock(
            x=self.width,
            y=y,
            size=SKY_BLOCK_SIZE,
            color=SKY_BLOCK_COLOR,
            speed=current_speed,
            sprite=_SKY_BLOCK_SPRITE,
        )
        self._sky_blocks.append(block)

    def _spawn_cloud(self, current_speed: float) -> None:
        """Create a new cloud at the right edge using drawn puffy ellipses."""
        width = random.randint(*CLOUD_SIZE_RANGE)
        height = max(width // 4, 8)
        y = random.randint(40, self._ground_y // 2)
        cloud = DrawnCloud(
            x=self.width,
            y=y,
            width=width,
            height=height,
            color=CLOUD_COLOR,
            speed=current_speed,
        )
        self._clouds.append(cloud)

    def _seed_clouds(self, current_speed: float) -> None:
        """Populate the moving cloud layer across the sky with drawn clouds."""
        for _ in range(5):
            width = random.randint(*CLOUD_SIZE_RANGE)
            height = max(width // 4, 8)
            y = random.randint(40, self._ground_y // 2)
            x = int(self.width * random.uniform(0.15, 0.95))
            cloud = DrawnCloud(
                x=x,
                y=y,
                width=width,
                height=height,
                color=CLOUD_COLOR,
                speed=current_speed,
            )
            self._clouds.append(cloud)

    def _draw_hud(self, frame: np.ndarray) -> None:
        """Draw coins, level, additive speed multiplier, player name, and hearts."""
        speed_mult = 1 + SPEED_INCREMENT * (self._obstacle_manager.level - 1)
        self._draw_hearts(frame)
        cv2.putText(
            frame, f"Jugador: {self._player_name}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, HUD_COLOR, 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Monedas: {self._coins}",
            (10, 48),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUD_COLOR, 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Nivel: {self._obstacle_manager.level}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Velocidad: {speed_mult:.1f}x",
            (10, 92),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

    def _render_game_over(self, frame: np.ndarray, connections: list) -> None:
        """Render game over screen with additive speed and total coins."""
        self._render_game(frame, connections)
        frame[:] = (frame * 0.4).astype(frame.dtype)

        speed_mult = 1 + SPEED_INCREMENT * (self._obstacle_manager.level - 1)

        cv2.putText(
            frame, "GAME OVER",
            (self.width // 2 - 80, self.height // 2 - 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Score: {self.passed_count}",
            (self.width // 2 - 40, self.height // 2 + 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUD_COLOR, 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Nivel: {self._obstacle_manager.level}",
            (self.width // 2 - 40, self.height // 2 + 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Velocidad: {speed_mult:.1f}x",
            (self.width // 2 - 40, self.height // 2 + 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
        cv2.putText(
            frame, f"Monedas: {self._coins}",
            (self.width // 2 - 40, self.height // 2 + 100),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )

        # Top 5 leaderboard (ordered by coins, cached at game over)
        title_y = self.height // 2 + 150
        cv2.putText(
            frame, "TOP 5",
            (self.width // 2 - 30, title_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA,
        )
        for i, (position, name, coins, level) in enumerate(self._leaderboard):
            row_y = title_y + 30 + i * 24
            row = f"{position}. {name}  {coins} monedas  N{level}"
            cv2.putText(
                frame, row,
                (self.width // 2 - 120, row_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, HUD_COLOR, 1, cv2.LINE_AA,
            )

        enter_y = title_y + 30 + len(self._leaderboard) * 24 + 20
        cv2.putText(
            frame, "Press ENTER to continue",
            (self.width // 2 - 100, enter_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA,
        )
