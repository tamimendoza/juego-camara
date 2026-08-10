"""MediaPipe PoseLandmarker wrapper for real-time multi-person body landmark detection.

Uses ``mediapipe.tasks.vision.PoseLandmarker`` with ``num_poses > 1`` to detect
multiple people in a single inference pass.  Each detected person produces a
``PoseResult`` with 33 body landmarks (head, arms, torso, legs) and an optional
segmentation mask.
"""

import os
import time
from dataclasses import dataclass
from typing import List, Optional

import mediapipe as mp
import numpy as np

from .utils import LandmarkPoint, landmarks_to_pixels, mp_image_to_numpy


@dataclass
class PoseResult:
    """Container for a single detected pose."""

    landmarks: Optional[List] = None
    segmentation_mask: Optional[np.ndarray] = None
    world_landmarks: Optional[List] = None
    success: bool = False

    def landmark_points(
        self, width: int, height: int, visibility_threshold: float = 0.5
    ) -> List[LandmarkPoint]:
        if self.landmarks is None:
            return []
        return landmarks_to_pixels(
            self.landmarks,
            width,
            height,
            visibility_threshold,
        )


class PoseDetector:
    """Real-time multi-person pose detector using MediaPipe PoseLandmarker.

    Args:
        model_path: Path to the ``.task`` model file (downloaded by run.sh).
        num_poses: Maximum number of people to detect per frame.
        min_pose_detection_confidence: Minimum confidence for pose detection.
        min_pose_presence_confidence: Minimum presence score for landmarks.
        min_tracking_confidence: Minimum confidence for pose tracking.
        output_segmentation_masks: Whether to output per-person segmentation masks.
    """

    def __init__(
        self,
        model_path: str = "models/pose_landmarker_lite.task",
        num_poses: int = 4,
        min_pose_detection_confidence: float = 0.5,
        min_pose_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        output_segmentation_masks: bool = True,
    ):
        from mediapipe.tasks.python.core import (
            base_options as base_options_module,
        )
        from mediapipe.tasks.python.vision import (
            PoseLandmarker,
            PoseLandmarkerOptions,
            RunningMode,
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}. "
                f"Run ./run.sh to download it automatically, "
                f"or set a custom model path."
            )

        base_options = base_options_module.BaseOptions(
            model_asset_path=model_path
        )
        options = PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.VIDEO,
            num_poses=num_poses,
            min_pose_detection_confidence=min_pose_detection_confidence,
            min_pose_presence_confidence=min_pose_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=output_segmentation_masks,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)
        self._last_timestamp: int = 0

    def detect(
        self,
        image: mp.Image,
        timestamp_ms: Optional[int] = None,
    ) -> List[PoseResult]:
        """Run multi-person pose detection on a video frame.

        Args:
            image: ``mp.Image`` in RGB format (use ``rgb_to_mp_image`` to convert
                from a numpy RGB array).
            timestamp_ms: Wall-clock timestamp in milliseconds for video
                frame sequencing.  If ``None``, auto-generates from
                ``time.time()`` ensuring monotonic increase.

        Returns:
            A list of ``PoseResult``, one per detected person.  An empty
            list means no person was detected.
        """
        if timestamp_ms is None:
            timestamp_ms = max(int(time.time() * 1000), self._last_timestamp + 1)
        self._last_timestamp = timestamp_ms

        result = self._landmarker.detect_for_video(image, timestamp_ms)

        pose_results: List[PoseResult] = []

        if not result.pose_landmarks:
            return pose_results

        for i, landmarks in enumerate(result.pose_landmarks):
            mask: Optional[np.ndarray] = None
            if (
                result.segmentation_masks is not None
                and i < len(result.segmentation_masks)
            ):
                mask = mp_image_to_numpy(result.segmentation_masks[i])

            world_landmarks: Optional[List] = None
            if (
                result.pose_world_landmarks
                and i < len(result.pose_world_landmarks)
            ):
                world_landmarks = result.pose_world_landmarks[i]

            pose_results.append(
                PoseResult(
                    landmarks=landmarks,
                    segmentation_mask=mask,
                    world_landmarks=world_landmarks,
                    success=True,
                )
            )

        return pose_results

    @property
    def connections(self):
        """MediaPipe POSE_CONNECTIONS for skeleton line drawing (33 landmarks)."""
        return mp.solutions.pose.POSE_CONNECTIONS

    def close(self) -> None:
        """Release the underlying MediaPipe PoseLandmarker resources."""
        self._landmarker.close()
