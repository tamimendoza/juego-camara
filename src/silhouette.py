"""Silhouette drawing for pose-based character rendering.

Provides two-layer drawing:
  1. Segmentation mask silhouette — the body outline filled with color
  2. Landmark-based skeleton — articulated body part polygons, lines, and joints
"""

import math

import cv2
import numpy as np
from typing import List, Optional, Sequence

from .utils import LIMB_TRIANGLES, LandmarkPoint, get_visible_polygon

# Face landmarks ordered clockwise around the perimeter for a proper polygon
_HEAD_PERIMETER = [7, 3, 2, 0, 9, 10, 4, 5, 6, 8]  # left_ear → left_eye → nose → mouth → right_eye → right_ear

# Maps LIMB_TRIANGLES keys to BODY_COLORS keys
_LIMB_COLOR_MAP = {
    "left_upper_arm": "left_arm",
    "right_upper_arm": "right_arm",
    "left_forearm": "left_arm",
    "right_forearm": "right_arm",
    "left_thigh": "left_leg",
    "right_thigh": "right_leg",
    "left_calf": "left_leg",
    "right_calf": "right_leg",
}

# Mario Bros character color palette (BGR)
MARIO_FACE = (200, 200, 255)    # peach face
MARIO_HAT = (0, 80, 255)        # red cap
MARIO_HAIR = (30, 30, 30)       # brown hair
MARIO_SHIRT = (0, 60, 255)      # red shirt
MARIO_OVERALL = (180, 0, 0)     # blue overalls

# Minecraft-themed colors (BGR)
MC_SKY = (235, 206, 135)        # sky blue (RGB 135,206,235)
MC_GRASS_TOP = (0, 180, 60)     # green grass block top (RGB 60,180,0)
MC_DIRT = (80, 60, 30)          # brown dirt block (RGB 30,60,80)
MC_CLOUD = (255, 255, 255)      # white clouds
MC_BLOCK_BORDER = (20, 20, 20)  # dark gray for voxel block edges
MC_EYE = (0, 0, 0)             # black pixel eyes


class SilhouetteDrawer:
    """Draws silhouettes and skeleton characters from pose landmarks."""

    BODY_COLORS = {
        "head": (255, 200, 200),
        "torso": (200, 255, 200),
        "left_arm": (200, 200, 255),
        "right_arm": (255, 200, 255),
        "left_leg": (200, 255, 255),
        "right_leg": (255, 255, 200),
    }

    def __init__(self):
        self.silhouette_color = (100, 140, 255)
        self.line_color = (80, 80, 80)
        self.joint_color = (255, 255, 255)
        self.line_thickness = 2
        self.joint_radius = 4

    # ------------------------------------------------------------------
    # Layer 1: Segmentation mask silhouette
    # ------------------------------------------------------------------

    @staticmethod
    def threshold_mask(mask: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Convert a MediaPipe float segmentation mask to a binary uint8 mask."""
        binary = (mask > threshold).astype(np.uint8) * 255
        return binary

    def fill_silhouette(
        self,
        frame: np.ndarray,
        mask_binary: np.ndarray,
        color: Optional[tuple] = None,
        alpha: float = 0.4,
    ) -> None:
        """Fill the person's body silhouette using the segmentation mask."""
        if mask_binary is None or mask_binary.size == 0:
            return
        contours, _ = cv2.findContours(
            mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 1000:
            return
        overlay = frame.copy()
        fill_color = color if color else self.silhouette_color
        cv2.fillConvexPoly(overlay, largest, fill_color)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def draw_silhouette_outline(
        self,
        frame: np.ndarray,
        mask_binary: np.ndarray,
        color: Optional[tuple] = None,
        thickness: int = 2,
    ) -> None:
        """Draw the person's silhouette outline from the segmentation mask."""
        if mask_binary is None or mask_binary.size == 0:
            return
        contours, _ = cv2.findContours(
            mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 1000:
            return
        outline_color = color if color else self.silhouette_color
        cv2.drawContours(frame, [largest], -1, outline_color, thickness)

    # ------------------------------------------------------------------
    # Layer 2: Landmark-based character skeleton
    # ------------------------------------------------------------------

    def draw_body_polygons(self, frame: np.ndarray, points: Sequence[LandmarkPoint]) -> None:
        """Draw filled body part polygons from landmark pixel coordinates."""
        # Torso quadrilateral (left_shoulder, right_shoulder, right_hip, left_hip)
        torso = get_visible_polygon(points, [11, 12, 24, 23])
        if torso and len(torso) >= 3:
            cv2.fillPoly(frame, [np.array(torso, dtype=np.int32)], self.BODY_COLORS["torso"])

        # Head polygon (face perimeter)
        head = get_visible_polygon(points, _HEAD_PERIMETER)
        if head and len(head) >= 3:
            cv2.fillPoly(frame, [np.array(head, dtype=np.int32)], self.BODY_COLORS["head"])

        # Limb triangles
        for part_name, indices in LIMB_TRIANGLES.items():
            tri = get_visible_polygon(points, indices)
            if tri and len(tri) >= 3:
                color_key = _LIMB_COLOR_MAP.get(part_name, part_name)
                color = self.BODY_COLORS.get(color_key, (255, 255, 255))
                cv2.fillPoly(frame, [np.array(tri, dtype=np.int32)], color)

    def draw_skeleton(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
        connections: List[tuple],
    ) -> None:
        """Draw lines between connected landmarks using POSE_CONNECTIONS."""
        for (i, j) in connections:
            if i < len(points) and j < len(points):
                p1, p2 = points[i], points[j]
                if p1 is not None and p2 is not None:
                    cv2.line(frame, p1, p2, self.line_color, self.line_thickness)

    def draw_joints(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
        radius: Optional[int] = None,
        color: Optional[tuple] = None,
        border: Optional[tuple] = None,
    ) -> None:
        """Draw filled circles at each visible landmark position."""
        r = radius if radius is not None else self.joint_radius
        c = color if color is not None else self.joint_color
        b = border if border is not None else self.line_color
        for p in points:
            if p is not None:
                cv2.circle(frame, p, r, c, -1)
                cv2.circle(frame, p, r + 1, b, 1)

    def draw_head_circle(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
    ) -> None:
        """Draw a single filled circle representing the head.

        The circle is centered at the nose landmark (index 0) with a
        radius proportional to the shoulder width (distance between
        landmarks 11 and 12).  If the nose or either shoulder is not
        visible, the head circle is omitted.
        """
        nose = points[0] if len(points) > 0 else None
        ls = points[11] if len(points) > 11 else None
        rs = points[12] if len(points) > 12 else None
        if nose is None or ls is None or rs is None:
            return
        shoulder_width = (
            (ls[0] - rs[0]) ** 2 + (ls[1] - rs[1]) ** 2
        ) ** 0.5
        radius = max(int(shoulder_width * 0.25), 10)
        cv2.circle(frame, nose, radius, self.joint_color, -1)

    def draw_body_lines(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
        connections: List[tuple],
    ) -> None:
        """Draw connection lines for body landmarks only (indices ≥ 11).

        Face connections (those involving landmarks 0–10) are excluded so
        that only the torso, arms, and legs are drawn as lines.
        """
        for (i, j) in connections:
            if i < 11 or j < 11:
                continue
            if i < len(points) and j < len(points):
                p1, p2 = points[i], points[j]
                if p1 is not None and p2 is not None:
                    cv2.line(frame, p1, p2, self.line_color, self.line_thickness)

    # ------------------------------------------------------------------
    # Layer 3: Mario Bros styled rendering
    # ------------------------------------------------------------------

    def draw_mario_head(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
    ) -> None:
        """Draw a Mario-style head: peach face circle + red cap + brown hair.

        Uses the nose landmark (index 0) as the face center and shoulder
        width (indices 11/12) to determine the head radius — same logic as
        ``draw_head_circle``. The cap is drawn above the face as a filled
        oval, and a small brown hair arc sits at the top of the face.
        """
        nose = points[0] if len(points) > 0 else None
        ls = points[11] if len(points) > 11 else None
        rs = points[12] if len(points) > 12 else None
        if nose is None or ls is None or rs is None:
            return
        shoulder_width = (
            (ls[0] - rs[0]) ** 2 + (ls[1] - rs[1]) ** 2
        ) ** 0.5
        radius = max(int(shoulder_width * 0.25), 10)

        # Face circle (peach)
        cv2.circle(frame, nose, radius, MARIO_FACE, -1)
        # Hair arc at top of face
        cv2.ellipse(
            frame, nose, (radius, radius), 0, 140, 40,
            MARIO_HAIR, max(int(radius * 0.3), 2),
        )
        # Cap: filled semi-oval above the face
        cap_center = (nose[0], nose[1] - radius)
        cv2.ellipse(
            frame, cap_center, (int(radius * 1.2), int(radius * 0.5)),
            0, 0, 180, MARIO_HAT, -1,
        )
        # Cap brim line
        cv2.line(
            frame,
            (cap_center[0] - int(radius * 1.2), cap_center[1]),
            (cap_center[0] + int(radius * 1.2), cap_center[1]),
            MARIO_HAT, 2,
        )

    def draw_mario_body(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
        connections: List[tuple],
    ) -> None:
        """Draw Mario's outfit as colored lines from landmark connections.

        Arm and torso connections (indices 11–22) are drawn red (shirt);
        leg connections (indices ≥ 23) are drawn blue (overalls). Face
        connections (indices < 11) are excluded.
        """
        for (i, j) in connections:
            if i < 11 or j < 11:
                continue
            if i >= len(points) or j >= len(points):
                continue
            p1, p2 = points[i], points[j]
            if p1 is None or p2 is None:
                continue
            # Legs use blue (overalls); everything else uses red (shirt)
            color = MARIO_OVERALL if (i >= 23 and j >= 23) else MARIO_SHIRT
            cv2.line(frame, p1, p2, color, max(self.line_thickness + 1, 3))

    # ------------------------------------------------------------------
    # Layer 3b: Face overlay rendering (real face crop)
    # ------------------------------------------------------------------

    def draw_face_overlay(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
        face_image: Optional[np.ndarray] = None,
        face_mask: Optional[np.ndarray] = None,
    ) -> None:
        """Overlay a cropped real face onto the character's head position.

        Uses the nose landmark (index 0) from PoseLandmarker as the head center
        and shoulder width (indices 11/12) to determine the head radius — same
        positioning logic as ``draw_mario_head``. The face_image is blended onto
        the frame using face_mask as an alpha channel.

        If face_image or face_mask is None, falls back to drawing a peach face
        circle (same as ``draw_mario_head``) so the character is always visible.
        """
        nose = points[0] if len(points) > 0 else None
        ls = points[11] if len(points) > 11 else None
        rs = points[12] if len(points) > 12 else None
        if nose is None or ls is None or rs is None:
            return

        shoulder_width = (
            (ls[0] - rs[0]) ** 2 + (ls[1] - rs[1]) ** 2
        ) ** 0.5
        radius = max(int(shoulder_width * 0.25), 10)

        if face_image is not None and face_mask is not None:
            from .face_crop import FaceCropper
            cropper = FaceCropper()
            cropper.overlay_face(frame, face_image, face_mask, nose, radius)
        else:
            # Fallback: peach face circle
            cv2.circle(frame, nose, radius, MARIO_FACE, -1)

    # ------------------------------------------------------------------
    # Layer 4: Minecraft voxel-style rendering
    # ------------------------------------------------------------------

    def _draw_oriented_rect(
        self,
        frame: np.ndarray,
        p1: LandmarkPoint,
        p2: LandmarkPoint,
        width: int,
        color: tuple,
        border: Optional[tuple] = None,
    ) -> None:
        """Draw a filled rectangle oriented along the line from p1 to p2.

        Produces a "thick line as a block" — the hallmark of Minecraft's voxel
        limb geometry.  The rectangle's long axis follows p1→p2 and its
        perpendicular half-width is *width* / 2.
        """
        if p1 is None or p2 is None:
            return
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length < 1:
            return
        px = -dy / length
        py = dx / length
        hw = width / 2.0
        corners = [
            (p1[0] + px * hw, p1[1] + py * hw),
            (p2[0] + px * hw, p2[1] + py * hw),
            (p2[0] - px * hw, p2[1] - py * hw),
            (p1[0] - px * hw, p1[1] - py * hw),
        ]
        pts = np.array(corners, dtype=np.int32)
        cv2.fillConvexPoly(frame, pts, color)
        if border is not None:
            cv2.polylines(frame, [pts], True, border, 1)

    def draw_minecraft_head(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
    ) -> None:
        """Draw a Minecraft-style head as a square voxel block.

        The block is centered at the nose landmark (index 0) and sized by
        shoulder width — same positioning logic as ``draw_head_circle``.
        The top ~35 % is a red cap block; the bottom ~65 % is a peach face
        block with two small black pixel eyes.  A dark border outlines the
        whole block for the voxel look.
        """
        nose = points[0] if len(points) > 0 else None
        ls = points[11] if len(points) > 11 else None
        rs = points[12] if len(points) > 12 else None
        if nose is None or ls is None or rs is None:
            return

        shoulder_width = (
            (ls[0] - rs[0]) ** 2 + (ls[1] - rs[1]) ** 2
        ) ** 0.5
        block_size = max(int(shoulder_width * 0.5), 20)
        half = block_size // 2

        cx, cy = nose
        x0 = cx - half
        y0 = cy - half
        x1 = cx + half
        y1 = cy + half

        # Cap block (top portion)
        cap_h = max(int(block_size * 0.35), 6)
        cv2.rectangle(frame, (x0, y0), (x1, y0 + cap_h), MARIO_HAT, -1)

        # Face block (bottom portion)
        cv2.rectangle(frame, (x0, y0 + cap_h), (x1, y1), MARIO_FACE, -1)

        # Pixel eyes (two small black squares in the face area)
        eye_size = max(block_size // 7, 2)
        eye_y = cy + cap_h + block_size // 4
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

        # Voxel block border
        cv2.rectangle(frame, (x0, y0), (x1, y1), MC_BLOCK_BORDER, 2)

    def draw_minecraft_body(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
        connections: List[tuple],
    ) -> None:
        """Draw Mario's outfit as Minecraft-style voxel blocks.

        Instead of thin lines, each body segment is a single **solid** oriented
        rectangle (block).  Five predefined segments are drawn directly from
        landmark indices — NOT derived from connection pairs — so each limb
        is one solid block rather than a chain of smaller rectangles:
          - Torso: shoulder midpoint → hip midpoint (red shirt)
          - Left arm: left shoulder (11) → left wrist (15) (red shirt)
          - Right arm: right shoulder (12) → right wrist (16) (red shirt)
          - Left leg: left hip (23) → left heel (27) (blue overalls)
          - Right leg: right hip (24) → right heel (28) (blue overalls)
        """
        ls = points[11] if len(points) > 11 else None  # left shoulder
        rs = points[12] if len(points) > 12 else None  # right shoulder
        lh = points[23] if len(points) > 23 else None  # left hip
        rh = points[24] if len(points) > 24 else None  # right hip

        lw = points[15] if len(points) > 15 else None  # left wrist
        rw = points[16] if len(points) > 16 else None  # right wrist
        lhz = points[27] if len(points) > 27 else None  # left heel
        rhz = points[28] if len(points) > 28 else None  # right heel

        block_w = max(self.line_thickness + 3, 8)

        # Torso block: shoulder center → hip center
        if ls is not None and rs is not None and lh is not None and rh is not None:
            shoulder_c = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
            hip_c = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
            self._draw_oriented_rect(
                frame, shoulder_c, hip_c,
                block_w, MARIO_SHIRT, MC_BLOCK_BORDER,
            )

        # Left arm block: left shoulder → left wrist
        if ls is not None and lw is not None:
            self._draw_oriented_rect(
                frame, ls, lw,
                block_w, MARIO_SHIRT, MC_BLOCK_BORDER,
            )

        # Right arm block: right shoulder → right wrist
        if rs is not None and rw is not None:
            self._draw_oriented_rect(
                frame, rs, rw,
                block_w, MARIO_SHIRT, MC_BLOCK_BORDER,
            )

        # Left leg block: left hip → left heel
        if lh is not None and lhz is not None:
            self._draw_oriented_rect(
                frame, lh, lhz,
                block_w, MARIO_OVERALL, MC_BLOCK_BORDER,
            )

        # Right leg block: right hip → right heel
        if rh is not None and rhz is not None:
            self._draw_oriented_rect(
                frame, rh, rhz,
                block_w, MARIO_OVERALL, MC_BLOCK_BORDER,
            )

    # ------------------------------------------------------------------
    # Full render entry point
    # ------------------------------------------------------------------

    def render_character(
        self,
        frame: np.ndarray,
        points: Sequence[LandmarkPoint],
        mask_binary: Optional[np.ndarray] = None,
        connections: Optional[List[tuple]] = None,
        styles: Optional[List[str]] = None,
        face_image: Optional[np.ndarray] = None,
        face_mask: Optional[np.ndarray] = None,
    ) -> None:
        """Render the full character on the frame.

        Layers (applied in order):
        1. "dark" — darken background (multiply by 0.15) for stick-figure mode
        2. "blank" — fill frame with solid black (no camera feed)
        3. Segmentation mask fill (if available)
        4. Body part polygons (colored limbs + head + torso)
        5. Skeleton connection lines (all landmarks)
        6. Joint markers
        7. "head_circle" — single filled circle at nose for the head
        8. "body_lines" — connection lines for body landmarks only (indices >= 11)
        9. "mario_head" — Mario-style head (peach face circle + red cap + brown hair)
        10. "mario_body" — Mario outfit lines (red shirt for arms/torus, blue overalls for legs)
        11. "face_overlay" — real face crop overlaid at nose position (replaces head)
        12. "minecraft_head" — Minecraft voxel head (square block: red cap top + peach face
            bottom + pixel eyes)
        13. "minecraft_body" — Minecraft voxel body (red/blue oriented rectangles for limbs)
        """
        if styles is None:
            styles = ["mask", "polygons", "skeleton", "joints"]

        if "dark" in styles:
            frame[:] = (frame * 0.15).astype(frame.dtype)

        if "blank" in styles:
            frame[:] = 0

        if "mask" in styles and mask_binary is not None:
            self.fill_silhouette(frame, mask_binary)
            self.draw_silhouette_outline(frame, mask_binary, thickness=3)

        if "polygons" in styles:
            self.draw_body_polygons(frame, points)

        if "skeleton" in styles and connections is not None:
            self.draw_skeleton(frame, points, connections)

        if "joints" in styles:
            self.draw_joints(frame, points)

        if "head_circle" in styles:
            self.draw_head_circle(frame, points)

        if "body_lines" in styles and connections is not None:
            self.draw_body_lines(frame, points, connections)

        if "mario_head" in styles:
            self.draw_mario_head(frame, points)

        if "mario_body" in styles and connections is not None:
            self.draw_mario_body(frame, points, connections)

        if "face_overlay" in styles:
            self.draw_face_overlay(frame, points, face_image, face_mask)

        if "minecraft_head" in styles:
            self.draw_minecraft_head(frame, points)

        if "minecraft_body" in styles and connections is not None:
            self.draw_minecraft_body(frame, points, connections)
