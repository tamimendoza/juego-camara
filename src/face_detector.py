"""MediaPipe FaceMesh wrapper for real-time face landmark detection.

Provides 468 face landmarks per detected face, running alongside the
existing PoseLandmarker pipeline. FaceMesh uses a model bundled with
mediapipe — no separate .task file download is required.
"""

from typing import List, Optional

import mediapipe as mp
import numpy as np


class FaceDetector:
    """Real-time face landmark detector using MediaPipe FaceMesh.

    Args:
        max_num_faces: Maximum number of faces to detect per frame.
        min_detection_confidence: Minimum confidence for face detection.
        min_tracking_confidence: Minimum confidence for face tracking.
    """

    def __init__(
        self,
        max_num_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=max_num_faces,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def detect(self, rgb_frame: np.ndarray) -> Optional[List]:
        """Run FaceMesh on an RGB numpy frame.

        Args:
            rgb_frame: RGB numpy array (H x W x 3, uint8).

        Returns:
            A list of 468 normalized face landmarks (each with x, y, z in
            [0, 1]) for the first detected face, or None if no face is found.
        """
        results = self._face_mesh.process(rgb_frame)
        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0]
        return None

    def close(self) -> None:
        """Release the underlying FaceMesh resources."""
        self._face_mesh.close()
