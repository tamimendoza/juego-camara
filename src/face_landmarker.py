"""MediaPipe Tasks API FaceLandmarker wrapper for real-time face landmark detection.

Uses the ``mediapipe.tasks.vision.FaceLandmarker`` with a ``.task`` model file
(falling back to the bundled FaceMesh solution API detector if the model file
is missing or incompatible).  Returns face landmarks and a computed face
bounding box, enabling tighter, more efficient face crops than the legacy
contour-landmark heuristic.
"""

import os
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from .utils import rgb_to_mp_image

PixelPoint = Tuple[int, int]
FaceBBox = Tuple[int, int, int, int]  # (x, y, width, height) in pixels


@dataclass
class FaceLandmarkResult:
    """Container for a single detected face."""

    landmarks: Optional[List] = None
    bbox: Optional[FaceBBox] = None  # pixel coords: (x, y, width, height)
    success: bool = False


class FaceLandmarkerDetector:
    """Real-time face landmark detector using MediaPipe Tasks API FaceLandmarker.

    Args:
        model_path: Path to the ``face_landmarker.task`` model file.
        num_faces: Maximum number of faces to detect per frame.
        min_face_detection_confidence: Minimum confidence for face detection.
        min_face_presence_confidence: Minimum presence score for landmarks.
        min_tracking_confidence: Minimum confidence for face tracking.
    """

    def __init__(
        self,
        model_path: str = "models/face_landmarker.task",
        num_faces: int = 1,
        min_face_detection_confidence: float = 0.5,
        min_face_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        from mediapipe.tasks.python.core import (
            base_options as base_options_module,
        )
        from mediapipe.tasks.python.vision import (
            FaceLandmarker,
            FaceLandmarkerOptions,
            RunningMode,
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Face landmark model file not found: {model_path}. "
                f"Run ./run_mario_face.sh to download it automatically, "
                f"or download face_landmarker.task manually."
            )

        base_options = base_options_module.BaseOptions(
            model_asset_path=model_path
        )
        options = FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.VIDEO,
            num_faces=num_faces,
            min_face_detection_confidence=min_face_detection_confidence,
            min_face_presence_confidence=min_face_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = FaceLandmarker.create_from_options(options)
        self._last_timestamp: int = 0

    def detect(
        self,
        rgb_frame: np.ndarray,
        timestamp_ms: Optional[int] = None,
    ) -> Tuple[Optional[List], Optional[FaceBBox]]:
        """Run face landmark detection on a video frame.

        Args:
            rgb_frame: RGB numpy array (H x W x 3, uint8).
            timestamp_ms: Wall-clock timestamp in milliseconds for video frame
                sequencing. If ``None``, auto-generates from ``time.time()``
                ensuring monotonic increase.

        Returns:
            A tuple of ``(face_landmarks, face_bbox)`` where:
            - ``face_landmarks``: list of NormalizedLandmark objects (468
              points) for the first detected face, or ``None`` if no face.
            - ``face_bbox``: bounding box as ``(x, y, width, height)`` in
              pixel coordinates, or ``None`` if no face or if the model does
              not provide bounding-box output.
        """
        if timestamp_ms is None:
            timestamp_ms = max(
                int(time.time() * 1000), self._last_timestamp + 1
            )
        self._last_timestamp = timestamp_ms

        height, width = rgb_frame.shape[:2]
        mp_image = rgb_to_mp_image(rgb_frame)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.face_landmarks:
            return None, None

        face_landmarks = result.face_landmarks[0]

        # Compute a face bounding box from landmarks (pixel coordinates).
        # In MediaPipe 0.10.3, FaceLandmarkerResult does not include
        # face_bounding_boxes, so we derive one from the 468 landmarks.
        face_bbox = self._compute_bbox(face_landmarks, width, height)

        return face_landmarks, face_bbox

    @staticmethod
    def _compute_bbox(
        landmarks: List, width: int, height: int
    ) -> Optional[FaceBBox]:
        """Compute a pixel bounding box from normalized face landmarks."""
        if not landmarks:
            return None
        xs = [lm.x * width for lm in landmarks]
        ys = [lm.y * height for lm in landmarks]
        x = int(min(xs))
        y = int(min(ys))
        w = int(max(xs) - x)
        h = int(max(ys) - y)
        if w < 1 or h < 1:
            return None
        return (x, y, w, h)

    def close(self) -> None:
        """Release the underlying MediaPipe FaceLandmarker resources."""
        self._landmarker.close()
