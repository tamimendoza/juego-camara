"""Face cropping utility for extracting a circular face region from a BGR frame.

Uses MediaPipe FaceMesh face contour landmarks to determine the face boundary,
then crops a circular region centered at the nose tip. The crop is returned
as a BGR image with a circular alpha mask, ready for overlay onto a character
head position.
"""

from typing import Optional, Tuple

import cv2
import numpy as np


class FaceCropper:
    """Extracts a circular face crop from a BGR camera frame using FaceMesh landmarks."""

    # FaceMesh face contour landmark indices (outer boundary of the face)
    # Indices 1-200 approximately trace the face contour
    _FACE_CONTOUR_INDICES = list(range(1, 201))

    # Nose tip landmark index in FaceMesh
    _NOSE_TIP = 1

    def crop_face(
        self,
        bgr_frame: np.ndarray,
        face_landmarks: list,
        width: int,
        height: int,
        target_radius: int,
        face_bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Crop a circular face region from the BGR camera frame.

        When ``face_bbox`` is provided (from the FaceLandmarker Tasks API), the
        crop is centered and sized from the bounding box for a tighter, more
        efficient crop.  When it is ``None`` (legacy FaceMesh path), the
        face contour landmarks are used to estimate the face boundary.

        Args:
            bgr_frame: The original BGR camera frame (H x W x 3).
            face_landmarks: List of 468 face landmarks (each with .x, .y in [0, 1]).
            width: Frame width in pixels.
            height: Frame height in pixels.
            target_radius: Desired radius of the circular face crop in pixels.
            face_bbox: Optional face bounding box as ``(x, y, width, height)``
                in pixel coordinates.  When provided, yields a tighter crop.

        Returns:
            A tuple of (face_image, face_mask) where:
            - face_image: BGR image of size (2*target_radius, 2*target_radius, 3)
            - face_mask: uint8 alpha mask of same spatial size (0 = transparent, 255 = opaque)
            Returns None if face_landmarks is None or empty.
        """
        if face_landmarks is None:
            return None

        # Convert FaceMesh normalized landmarks to pixel coordinates
        # face_landmarks is a NormalizedLandmarkList; .landmark holds the
        # actual list of NormalizedLandmark objects
        landmarks = getattr(face_landmarks, "landmark", face_landmarks)
        face_points = []
        for lm in landmarks:
            px = int(lm.x * width)
            py = int(lm.y * height)
            face_points.append((px, py))

        if len(face_points) <= self._NOSE_TIP:
            return None

        if face_bbox is not None:
            # Use the face bounding box for a tighter, more efficient crop
            bx, by, bw, bh = face_bbox
            nose_x = bx + bw // 2
            nose_y = by + bh // 2
            face_radius = max(int(max(bw, bh) * 0.5), target_radius)
        else:
            # Legacy path: use nose tip as center, contour landmarks for width
            nose_x, nose_y = face_points[self._NOSE_TIP]

            # Determine face size from face contour landmarks
            # Use the horizontal spread of the face contour to estimate face width
            contour_points = [
                face_points[i] for i in self._FACE_CONTOUR_INDICES
                if i < len(face_points)
            ]

            if len(contour_points) < 3:
                # Fallback: use a fixed radius based on target
                face_width = target_radius * 2
            else:
                xs = [p[0] for p in contour_points]
                face_width = max(xs) - min(xs)

            # Face radius: use face_width / 2 as the crop radius, then scale to target
            # This ensures the full face fits in the crop
            face_radius = max(int(face_width * 0.45), target_radius)

        # Crop a square region centered at the nose, sized to 2 * face_radius
        crop_size = face_radius * 2
        x0 = max(0, nose_x - face_radius)
        y0 = max(0, nose_y - face_radius)
        x1 = min(width, nose_x + face_radius)
        y1 = min(height, nose_y + face_radius)

        # Adjust crop to be square (handle edge clipping)
        actual_w = x1 - x0
        actual_h = y1 - y0
        crop_size = min(actual_w, actual_h)

        if crop_size < 10:
            return None

        # Re-center the crop
        half = crop_size // 2
        cx = max(half, min(width - half, nose_x))
        cy = max(half, min(height - half, nose_y))
        x0 = cx - half
        y0 = cy - half
        x1 = cx + half
        y1 = cy + half

        # Extract the face region
        face_region = bgr_frame[y0:y1, x0:x1].copy()

        if face_region.size == 0:
            return None

        # Resize to target size (2 * target_radius square)
        target_size = target_radius * 2
        face_resized = cv2.resize(face_region, (target_size, target_size), interpolation=cv2.INTER_LINEAR)

        # Create circular mask
        mask = np.zeros((target_size, target_size), dtype=np.uint8)
        cv2.circle(mask, (target_radius, target_radius), target_radius, 255, -1)

        return face_resized, mask

    def overlay_face(
        self,
        frame: np.ndarray,
        face_image: np.ndarray,
        face_mask: np.ndarray,
        center: Tuple[int, int],
        target_radius: int,
    ) -> None:
        """Overlay a cropped face onto a frame at the given center position.

        Args:
            frame: The destination BGR frame to draw onto.
            face_image: The cropped face BGR image.
            face_mask: Alpha mask for the face (0 = transparent, 255 = opaque).
            center: (x, y) pixel position for the face center.
            target_radius: Radius of the face circle in the destination frame.
        """
        if face_image is None or face_mask is None:
            return

        cx, cy = center
        r = target_radius

        # Resize face to target size
        target_size = r * 2
        face_resized = cv2.resize(face_image, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
        mask_resized = cv2.resize(face_mask, (target_size, target_size), interpolation=cv2.INTER_LINEAR)

        # Calculate region of interest
        x0 = cx - r
        y0 = cy - r
        x1 = cx + r
        y1 = cy + r

        # Clamp to frame bounds
        frame_h, frame_w = frame.shape[:2]
        x0_clamped = max(0, x0)
        y0_clamped = max(0, y0)
        x1_clamped = min(frame_w, x1)
        y1_clamped = min(frame_h, y1)

        # Calculate corresponding face region
        fx0 = x0_clamped - x0
        fy0 = y0_clamped - y0
        fx1 = fx0 + (x1_clamped - x0_clamped)
        fy1 = fy0 + (y1_clamped - y0_clamped)

        if fx1 <= fx0 or fy1 <= fy0:
            return

        roi = frame[y0_clamped:y1_clamped, x0_clamped:x1_clamped]
        face_roi = face_resized[fy0:fy1, fx0:fx1]
        mask_roi = mask_resized[fy0:fy1, fx0:fx1]

        # Blend face onto frame using mask
        alpha = mask_roi.astype(float) / 255.0
        alpha_3ch = np.stack([alpha, alpha, alpha], axis=2)
        frame[y0_clamped:y1_clamped, x0_clamped:x1_clamped] = (
            roi * (1 - alpha_3ch) + face_roi * alpha_3ch
        ).astype(np.uint8)
