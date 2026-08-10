"""Unit tests for PoseDetector multi-pose detection (mock-based)."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.pose_detector import PoseDetector, PoseResult
from src.utils import mp_image_to_numpy


class FakeLandmark:
    """A minimal landmark object compatible with landmarks_to_pixels."""

    def __init__(self, x=0.5, y=0.5, visibility=1.0, presence=1.0):
        self.x = x
        self.y = y
        self.visibility = visibility
        self.presence = presence


class FakeMpImage:
    """Mock mp.Image that supports numpy_view() for mask conversion."""

    def __init__(self, array: np.ndarray):
        self._array = array

    def numpy_view(self):
        return self._array


class FakeLandmarkerResult:
    """Mock of PoseLandmarkerResult for testing."""

    def __init__(
        self,
        pose_landmarks=None,
        pose_world_landmarks=None,
        segmentation_masks=None,
    ):
        self.pose_landmarks = pose_landmarks or []
        self.pose_world_landmarks = pose_world_landmarks
        self.segmentation_masks = segmentation_masks


def make_landmarks(n=33, x=0.5, y=0.5):
    """Create n fake landmarks at normalized position (x, y)."""
    return [FakeLandmark(x, y) for _ in range(n)]


def make_detector_with_mock_landmarker():
    """Create a PoseDetector that bypasses __init__ (no model file needed)."""
    detector = PoseDetector.__new__(PoseDetector)
    detector._landmarker = MagicMock()
    detector._last_timestamp = 0
    return detector


class TestDetectNoPoses:
    def test_empty_pose_list_returns_empty_list(self):
        detector = make_detector_with_mock_landmarker()
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult(
            pose_landmarks=[]
        )
        results = detector.detect(MagicMock())
        assert results == []

    def test_none_pose_landmarks_returns_empty_list(self):
        detector = make_detector_with_mock_landmarker()
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult(
            pose_landmarks=None
        )
        results = detector.detect(MagicMock())
        assert results == []


class TestDetectSinglePose:
    def test_single_pose_returns_one_result(self):
        detector = make_detector_with_mock_landmarker()
        landmarks = make_landmarks()
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult(
            pose_landmarks=[landmarks]
        )
        results = detector.detect(MagicMock())
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].landmarks == landmarks

    def test_single_pose_no_segmentation_mask(self):
        detector = make_detector_with_mock_landmarker()
        landmarks = make_landmarks()
        result = FakeLandmarkerResult(
            pose_landmarks=[landmarks],
            segmentation_masks=None,
        )
        detector._landmarker.detect_for_video.return_value = result
        results = detector.detect(MagicMock())
        assert results[0].segmentation_mask is None

    def test_single_pose_with_segmentation_mask(self):
        detector = make_detector_with_mock_landmarker()
        landmarks = make_landmarks()
        fake_mask = np.random.rand(480, 640).astype(np.float32)
        mask_image = FakeMpImage(fake_mask)
        result = FakeLandmarkerResult(
            pose_landmarks=[landmarks],
            segmentation_masks=[mask_image],
        )
        detector._landmarker.detect_for_video.return_value = result
        results = detector.detect(MagicMock())
        assert results[0].segmentation_mask is not None
        np.testing.assert_array_equal(
            results[0].segmentation_mask, mp_image_to_numpy(mask_image)
        )


class TestDetectMultiplePoses:
    def test_two_poses_return_two_results(self):
        detector = make_detector_with_mock_landmarker()
        lm1 = make_landmarks(x=0.3, y=0.3)
        lm2 = make_landmarks(x=0.7, y=0.7)
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult(
            pose_landmarks=[lm1, lm2]
        )
        results = detector.detect(MagicMock())
        assert len(results) == 2
        assert results[0].landmarks == lm1
        assert results[1].landmarks == lm2

    def test_all_results_have_success_true(self):
        detector = make_detector_with_mock_landmarker()
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult(
            pose_landmarks=[make_landmarks(), make_landmarks(), make_landmarks()]
        )
        results = detector.detect(MagicMock())
        assert all(r.success for r in results)

    def test_world_landmarks_passed_through(self):
        detector = make_detector_with_mock_landmarker()
        landmarks = make_landmarks()
        world_lms = make_landmarks(x=1.0, y=1.0)
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult(
            pose_landmarks=[landmarks],
            pose_world_landmarks=[world_lms],
        )
        results = detector.detect(MagicMock())
        assert results[0].world_landmarks == world_lms


class TestDetectTimestamp:
    def test_auto_generates_timestamp(self):
        """detect() generates a timestamp when one is not provided."""
        detector = make_detector_with_mock_landmarker()
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult()
        detector.detect(MagicMock())
        call_args = detector._landmarker.detect_for_video.call_args
        assert call_args is not None
        assert len(call_args[0]) == 2  # image + timestamp_ms

    def test_explicit_timestamp_used(self):
        """detect() uses the provided timestamp."""
        detector = make_detector_with_mock_landmarker()
        detector._landmarker.detect_for_video.return_value = FakeLandmarkerResult()
        detector.detect(MagicMock(), timestamp_ms=12345)
        call_args = detector._landmarker.detect_for_video.call_args
        assert call_args[0][1] == 12345


class TestPoseDetectorConnections:
    def test_connections_returns_pose_connections(self):
        """The connections property returns MediaPipe POSE_CONNECTIONS."""
        import mediapipe as mp

        # Can't create a real PoseDetector without model file, but connections
        # is a class-level constant accessible via mp.solutions.pose
        connections = set(mp.solutions.pose.POSE_CONNECTIONS)
        assert (11, 13) in connections  # left shoulder → left elbow
        assert (12, 14) in connections  # right shoulder → right elbow
        assert (23, 25) in connections  # left hip → left knee
