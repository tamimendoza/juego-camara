"""Character module: ties together pose detection, smoothing, silhouette rendering,
and keyboard controls for the mimicking character(s)."""

from typing import List, Optional, Sequence

import numpy as np

from .silhouette import SilhouetteDrawer
from .utils import LandmarkPoint, smooth_landmarks

# Distinct colors (BGR) for each person's character, so multiple people
# are visually distinguishable on screen.
CHARACTER_COLORS = [
    (255, 255, 255),  # white  (person 0)
    (0, 0, 255),      # red    (person 1)
    (0, 255, 0),      # green  (person 2)
    (255, 0, 0),      # blue   (person 3)
]


# Symmetric left/right landmark index pairs for mirror mode.
# In a real mirror left and right are swapped; the X-flip is applied on top
# so that limb directions are preserved relative to the body centerline.
# Head/face landmarks (0–10) are intentionally omitted — they are
# midline or asymmetric and only get X-flipped.
_MIRROR_LANDMARK_MAP: dict = {
    11: 12, 12: 11,   # shoulders
    13: 14, 14: 13,   # elbows
    15: 16, 16: 15,   # wrists
    17: 18, 18: 17,   # pinkies
    19: 20, 20: 19,   # index fingers
    21: 22, 22: 21,   # thumbs
    23: 24, 24: 23,   # hips
    25: 26, 26: 25,   # knees
    27: 28, 28: 27,   # ankles
    29: 30, 30: 29,   # heels
    31: 32, 32: 31,   # foot indices
}


def mirror_points(points: Sequence[LandmarkPoint], width: int) -> List[LandmarkPoint]:
    """Mirror landmark points horizontally for mirror mode.

    Swaps symmetric left/right landmark indices *first*, then X-flips the
    coordinates. This preserves limb direction relative to the body centerline
    (e.g., an arm extended backward stays backward in the mirrored character),
    matching real-mirror behavior rather than reversing every direction.
    """
    mirrored: List[LandmarkPoint] = []
    for i in range(len(points)):
        source = _MIRROR_LANDMARK_MAP.get(i, i)
        if source >= len(points):
            mirrored.append(None)
            continue
        p = points[source]
        if p is None:
            mirrored.append(None)
        else:
            mirrored.append((width - p[0], p[1]))
    return mirrored


class MimicCharacter:
    """A character that mimics one person's pose in real time.

    Tracks smoothed landmark positions, applies optional mirroring, and
    renders a colored silhouette + skeleton onto the camera frame.
    """

    # Rendering style presets (subset of SilhouetteDrawer.render_character layers)
    STYLES = [
        ["mask", "polygons", "skeleton", "joints"],    # full silhouette + skeleton
        ["polygons", "skeleton", "joints"],            # body polygons + skeleton
        ["skeleton", "joints"],                        # skeleton + joints only
        ["dark", "skeleton", "joints"],                # stick figure on dimmed camera feed
        ["blank", "skeleton", "joints"],               # stick figure on black background (no person visible)
        ["blank", "head_circle", "body_lines"],        # head circle + body lines on solid background
    ]

    def __init__(
        self,
        width: int,
        height: int,
        smooth_alpha: float = 0.3,
        color_index: int = 0,
        style_index: int = 0,
    ):
        self.width = width
        self.height = height
        self._smoother_alpha = smooth_alpha
        self._drawer = SilhouetteDrawer()
        self._prev_points: Optional[List[LandmarkPoint]] = None
        self._points: Optional[List[LandmarkPoint]] = None
        self._mask_binary: Optional[np.ndarray] = None
        self._connections: Optional[List[tuple]] = None
        self._pose_success: bool = False
        self.mirror_mode: bool = False
        self._style_index: int = style_index

        # Per-character color (for multi-person rendering)
        color = CHARACTER_COLORS[color_index % len(CHARACTER_COLORS)]
        self._drawer.line_color = color
        self._drawer.joint_color = color
        self._drawer.silhouette_color = color

    def update(
        self,
        pose_result,
        connections: Optional[List[tuple]] = None,
    ) -> None:
        """Update character state from pose detection results.

        Applies EMA smoothing to landmark coordinates. When the user is
        not detected, previous points are cleared so no ghosting occurs.
        """
        if not pose_result.success:
            self._prev_points = None
            self._points = None
            self._mask_binary = None
            self._pose_success = False
            return

        raw_points = pose_result.landmark_points(
            self.width, self.height, visibility_threshold=0.5
        )

        smoothed = smooth_landmarks(self._prev_points, raw_points, alpha=self._smoother_alpha)

        # Keep the smoother state in the raw (non-mirrored) coordinate frame.
        # Mirroring after smoothing prevents the EMA from blending mirrored
        # previous points with raw current points, which would pull the
        # character back toward the unmirrored position over a few frames.
        self._prev_points = smoothed

        if self.mirror_mode:
            smoothed = mirror_points(smoothed, self.width)
        self._points = smoothed
        self._connections = connections
        self._pose_success = True

        if pose_result.segmentation_mask is not None:
            self._mask_binary = self._drawer.threshold_mask(pose_result.segmentation_mask)
        else:
            self._mask_binary = None

    def render(
        self,
        frame: np.ndarray,
        styles: Optional[List[str]] = None,
    ) -> None:
        """Render the character silhouette and skeleton onto the frame."""
        if not self._pose_success or self._points is None:
            return

        if styles is None:
            styles = self.STYLES[self._style_index]

        self._drawer.render_character(
            frame,
            self._points,
            mask_binary=self._mask_binary,
            connections=self._connections,
            styles=styles,
        )

    def toggle_mirror(self) -> bool:
        """Toggle mirror mode. Returns the new state."""
        self.mirror_mode = not self.mirror_mode
        return self.mirror_mode

    def cycle_style(self) -> int:
        """Cycle to the next rendering style. Returns the new style index."""
        self._style_index = (self._style_index + 1) % len(self.STYLES)
        return self._style_index

    @property
    def style_name(self) -> str:
        style = self.STYLES[self._style_index]
        return ", ".join(style) if style else "none"


class CharacterManager:
    """Manages multiple ``MimicCharacter`` instances for multi-person tracking.

    Creates a character when a new person appears, updates existing
    characters with matched pose data, and removes characters when people
    leave the frame.  Each character gets a distinct color from
    ``CHARACTER_COLORS``.
    """

    def __init__(
        self,
        width: int,
        height: int,
        max_persons: int = 4,
        smooth_alpha: float = 0.3,
    ):
        self.width = width
        self.height = height
        self._max_persons = max_persons
        self._smooth_alpha = smooth_alpha
        self._characters: List[MimicCharacter] = []
        self._connections: Optional[List[tuple]] = None
        self._style_index: int = 0
        self._mirror_mode: bool = False

    def update(
        self,
        pose_results: List,
        connections: Optional[List[tuple]] = None,
    ) -> None:
        """Update characters from multi-person pose detection results.

        Args:
            pose_results: List of ``PoseResult`` (one per detected person).
            connections: MediaPipe POSE_CONNECTIONS for skeleton lines.
        """
        self._connections = connections

        num_poses = min(len(pose_results), self._max_persons)

        # Create new characters for newly detected people
        while len(self._characters) < num_poses:
            idx = len(self._characters)
            char = MimicCharacter(
                self.width,
                self.height,
                self._smooth_alpha,
                color_index=idx,
                style_index=self._style_index,
            )
            char.mirror_mode = self._mirror_mode
            self._characters.append(char)

        # Remove characters for people no longer detected
        while len(self._characters) > num_poses:
            self._characters.pop()

        # Update each character with its corresponding pose result
        for char, pose_result in zip(self._characters, pose_results[:num_poses]):
            char.update(pose_result, connections)

    def render(self, frame: np.ndarray) -> None:
        """Render all active characters on the frame.

        Background styles (``blank`` / ``dark``) are applied once for the
        whole frame so that they don't overwrite previously drawn characters.
        Each character then renders only its drawing layers.
        """
        if not self._characters:
            return

        styles = MimicCharacter.STYLES[self._style_index]

        # Apply background styles once
        if "dark" in styles:
            frame[:] = (frame * 0.15).astype(frame.dtype)
        if "blank" in styles:
            frame[:] = 0

        # Render each character's drawing layers only
        drawing_styles = [s for s in styles if s not in ("blank", "dark")]
        for char in self._characters:
            char.render(frame, styles=drawing_styles)

    def cycle_style(self) -> int:
        """Cycle rendering style for all characters. Returns the new style index."""
        self._style_index = (self._style_index + 1) % len(MimicCharacter.STYLES)
        for char in self._characters:
            char._style_index = self._style_index
        return self._style_index

    def toggle_mirror(self) -> bool:
        """Toggle mirror mode for all characters. Returns the new state."""
        self._mirror_mode = not self._mirror_mode
        for char in self._characters:
            char.mirror_mode = self._mirror_mode
        return self._mirror_mode

    @property
    def style_name(self) -> str:
        style = MimicCharacter.STYLES[self._style_index]
        return ", ".join(style) if style else "none"

    @property
    def num_people(self) -> int:
        """Number of currently tracked characters."""
        return len(self._characters)
