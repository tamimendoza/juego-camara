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
    python3 -m src.mario_face_main
    # or: ./run_mario_face.sh
"""

from typing import Optional

import cv2
import numpy as np

from .face_landmarker import FaceLandmarkerDetector
from .face_crop import FaceCropper
from .mario_game import (
    MarioCharacter,
    MarioGameEngine,
    RESOLUTION,
    WINDOW_NAME,
    SKY_COLOR,
    HUD_COLOR,
    POSE_WARNING_TEXT,
    POSE_WARNING_COLOR,
)


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
            styles = ["mario_body", "face_overlay"]
        else:
            styles = ["mario_head", "mario_body"]

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

    def __init__(
        self,
        width: int,
        height: int,
        sound_manager,
        face_landmarker: FaceLandmarkerDetector,
        face_cropper: FaceCropper,
    ):
        super().__init__(width, height, sound_manager)
        self._player = MarioFaceCharacter(
            self._player.x, self._player.ground_y,
        )
        self._face_landmarker = face_landmarker
        self._face_cropper = face_cropper
        self._face_image: np.ndarray = None
        self._face_mask: np.ndarray = None

    def detect_face(self, rgb_frame: np.ndarray, bgr_frame: np.ndarray) -> None:
        """Run FaceLandmarker detection and crop the face from the camera frame.

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
        else:
            self._face_image = None
            self._face_mask = None

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

    def _render_game(self, frame: np.ndarray, connections: list) -> None:
        """Render the playing game state with face overlay on the character.

        Mirrors the parent's ``_render_game`` but passes the face crop to the
        player's render method for the face overlay.
        """
        frame[:] = (200, 230, 255)

        for cloud in self._clouds:
            cloud.render(frame)

        for block in self._sky_blocks:
            block.render(frame)

        self._render_static_environment(frame, draw_clouds=False)

        self._obstacle_manager.render(frame)

        self._player.render(
            frame,
            connections,
            face_image=self._face_image,
            face_mask=self._face_mask,
        )

        self._draw_hud(frame)

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
        self._render_static_environment(frame)

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
