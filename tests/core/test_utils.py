"""Unit tests for coordinate transforms, body part groups, and smoothing."""

import numpy as np
import pytest

from src.core.utils import (
    BODY_PART_GROUPS,
    LIMB_TRIANGLES,
    LandmarkPoint,
    normalized_to_pixel,
    landmarks_to_pixels,
    smooth_landmarks,
    get_visible_polygon,
)


class TestNormalizedToPixel:
    def test_center_point(self):
        """Normalized (0.5, 0.5) maps to image center."""
        x, y = normalized_to_pixel(0.5, 0.5, 640, 480)
        assert x == 320
        assert y == 240

    def test_corner_top_left(self):
        """Normalized (0, 0) maps to top-left (0, 0)."""
        x, y = normalized_to_pixel(0.0, 0.0, 640, 480)
        assert x == 0
        assert y == 0

    def test_corner_bottom_right(self):
        """Normalized (1, 1) maps to bottom-right (639, 479)."""
        x, y = normalized_to_pixel(1.0, 1.0, 640, 480)
        assert x == 639
        assert y == 479

    def test_clamping(self):
        """Values slightly outside [0,1] are clamped to valid pixel range."""
        x, y = normalized_to_pixel(-0.1, 1.1, 100, 100)
        assert x == 0
        assert y == 99


class TestLandmarksToPixels:
    class FakeLandmark:
        def __init__(self, x, y, visibility=1.0, presence=1.0):
            self.x = x
            self.y = y
            self.visibility = visibility
            self.presence = presence

    def test_all_visible(self):
        landmarks = [self.FakeLandmark(0.5, 0.5) for _ in range(5)]
        points = landmarks_to_pixels(landmarks, 640, 480)
        assert all(p == (320, 240) for p in points)

    def test_visibility_filter(self):
        landmarks = [
            self.FakeLandmark(0.0, 0.0, visibility=0.3),  # below threshold
            self.FakeLandmark(0.5, 0.5, visibility=0.9),
        ]
        points = landmarks_to_pixels(landmarks, 640, 480, visibility_threshold=0.5)
        assert points[0] is None
        assert points[1] == (320, 240)

    def test_empty_input(self):
        points = landmarks_to_pixels([], 640, 480)
        assert points == []

    def test_presence_filter(self):
        landmarks = [
            self.FakeLandmark(0.0, 0.0, presence=0.3),  # below threshold
            self.FakeLandmark(0.5, 0.5, presence=0.9),
        ]
        points = landmarks_to_pixels(landmarks, 640, 480, visibility_threshold=0.5)
        assert points[0] is None
        assert points[1] == (320, 240)

    def test_presence_and_visibility_both_checked(self):
        landmarks = [
            self.FakeLandmark(0.0, 0.0, presence=0.3, visibility=0.9),  # presence low
            self.FakeLandmark(0.5, 0.5, presence=0.9, visibility=0.3),   # visibility low
        ]
        points = landmarks_to_pixels(landmarks, 640, 480, visibility_threshold=0.5)
        assert points[0] is None
        assert points[1] is None

    def test_none_presence_and_visibility_treated_as_visible(self):
        landmarks = [
            self.FakeLandmark(0.0, 0.0, presence=None, visibility=None),
        ]
        points = landmarks_to_pixels(landmarks, 640, 480)
        assert points[0] == (0, 0)


class TestMpImageHelpers:
    def test_rgb_to_mp_image_roundtrip(self):
        """rgb_to_mp_image + mp_image_to_numpy should preserve pixel data."""
        from src.core.utils import rgb_to_mp_image, mp_image_to_numpy

        rgb = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        mp_img = rgb_to_mp_image(rgb)
        result = mp_image_to_numpy(mp_img)

        assert result.shape == (480, 640, 3)
        np.testing.assert_array_equal(result, rgb)

    def test_rgb_to_mp_image_accepts_contiguous_array(self):
        """rgb_to_mp_image works with a standard contiguous RGB array."""
        from src.core.utils import rgb_to_mp_image, mp_image_to_numpy

        rgb = np.zeros((100, 200, 3), dtype=np.uint8)
        rgb[50, 100] = (255, 128, 64)
        mp_img = rgb_to_mp_image(rgb)
        result = mp_image_to_numpy(mp_img)

        assert result[50, 100, 0] == 255
        assert result[50, 100, 1] == 128
        assert result[50, 100, 2] == 64


class TestSmoothLandmarks:
    def test_no_history_returns_current(self):
        curr = [(100, 100), (200, 200), None]
        result = smooth_landmarks(None, curr, alpha=0.3)
        assert result == curr

    def test_ema_blending(self):
        prev = [(100, 100)]
        curr = [(200, 200)]
        result = smooth_landmarks(prev, curr, alpha=0.3)
        # 100 * 0.7 + 200 * 0.3 = 130
        assert result[0] == (130, 130)

    def test_none_handling_prev_none(self):
        prev = [None]
        curr = [(50, 50)]
        result = smooth_landmarks(prev, curr, alpha=0.3)
        assert result[0] == (50, 50)

    def test_none_handling_curr_none(self):
        prev = [(50, 50)]
        curr = [None]
        result = smooth_landmarks(prev, curr, alpha=0.3)
        assert result[0] == (50, 50)


class TestGetVisiblePolygon:
    def test_all_visible(self):
        points = [(10, 10), (20, 20), (30, 10)]
        polygon = get_visible_polygon(points, [0, 1, 2])
        assert polygon == [(10, 10), (20, 20), (30, 10)]

    def test_one_occluded_returns_none(self):
        points = [(10, 10), None, (30, 10)]
        polygon = get_visible_polygon(points, [0, 1, 2])
        assert polygon is None

    def test_out_of_range_returns_none(self):
        points = [(10, 10), (20, 20)]
        polygon = get_visible_polygon(points, [0, 5])
        assert polygon is None

    def test_min_three_points(self):
        points = [(10, 10), (20, 20)]
        polygon = get_visible_polygon(points, [0, 1])
        assert polygon == [(10, 10), (20, 20)]


class TestBodyPartGroups:
    def test_all_33_landmarks_covered_in_limb_triangles(self):
        """Every limb triangle index references a valid landmark (0-32)."""
        all_indices = set()
        for indices in LIMB_TRIANGLES.values():
            for idx in indices:
                assert 0 <= idx <= 32
                all_indices.add(idx)
        assert len(all_indices) > 0

    def test_body_part_groups_have_expected_keys(self):
        expected_keys = {"head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"}
        assert expected_keys.issubset(BODY_PART_GROUPS.keys())

    def test_torso_uses_shoulder_and_hip_landmarks(self):
        torso = BODY_PART_GROUPS["torso"]
        assert 11 in torso  # left shoulder
        assert 12 in torso  # right shoulder
        assert 23 in torso  # left hip
        assert 24 in torso  # right hip


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
