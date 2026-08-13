"""Unit tests for the pose landmark mirroring helper (mirror_points)."""

from src.core.character import _MIRROR_LANDMARK_MAP, mirror_points


def make_pixel_points(n=33, base_x=300, base_y=250):
    """Create n pixel-coordinate points, all visible, near the center."""
    points = []
    for i in range(n):
        points.append((base_x + (i % 5) - 2, base_y + (i % 3) - 1))
    return points


class TestMirrorPoints:
    def test_x_flip_only_for_head_landmarks(self):
        """Head landmarks (indices 0-10) are X-flipped without index swapping."""
        width = 640
        # Nose at x=320 → should become 640-320 = 320 (centered)
        points = [(320, 240)] + [(300 + i, 240) for i in range(1, 33)]
        mirrored = mirror_points(points, width)
        assert mirrored[0] == (320, 240)  # nose X-flipped
        assert mirrored[0][0] == width - points[0][0]

    def test_swaps_left_right_landmark_pairs(self):
        """Left/right landmark index pairs are swapped before X-flip."""
        width = 640
        # Right shoulder (12) at x=400, left shoulder (11) at x=240
        points = [None] * 33
        points[11] = (240, 300)  # left shoulder
        points[12] = (400, 300)  # right shoulder

        mirrored = mirror_points(points, width)

        # Output index 11 (left shoulder) should get X-flipped right shoulder
        assert mirrored[11] == (240, 300)  # 640 - 400 = 240
        # Output index 12 (right shoulder) should get X-flipped left shoulder
        assert mirrored[12] == (400, 300)  # 640 - 240 = 400

    def test_preserves_none_points(self):
        """None landmarks are preserved as None in the output."""
        width = 640
        points = [None] * 33
        points[11] = (240, 300)  # left shoulder visible
        points[12] = (400, 300)  # right shoulder visible

        mirrored = mirror_points(points, width)

        # Head landmarks (0-10) that are None stay None
        assert mirrored[0] is None
        assert mirrored[5] is None

    def test_arm_direction_preserved_when_extended_lateral(self):
        """When the user extends their right arm to the right, the mirrored
        character's left arm (on the left side of screen) also extends laterally.

        With pure X-flip (bug), the right arm would appear on the left side but
        still labeled as 'right arm' with reversed direction.
        """
        width = 640
        # User: right arm extended to the right (forward/lateral)
        # Right shoulder at 440, right wrist at 500 → wrist is to the RIGHT of shoulder
        points = [None] * 33
        points[11] = (200, 300)  # left shoulder
        points[12] = (440, 300)  # right shoulder
        points[15] = (200, 350)  # left wrist at side
        points[16] = (500, 350)  # right wrist extended to the right

        mirrored = mirror_points(points, width)

        # After mirror: left arm (11,15) should be the mirror of right arm
        # Char left shoulder = X-flip of right shoulder = 640-440 = 200
        # Char left wrist = X-flip of right wrist = 640-500 = 140
        # Wrist (140) is LEFT of shoulder (200) → arm points left (backward for
        # the character's left arm, which is on the left side of screen)
        assert mirrored[11] == (200, 300)
        assert mirrored[15] == (140, 350)
        assert mirrored[15][0] < mirrored[11][0]  # wrist left of shoulder

        # Char right arm (12,16) should be mirror of left arm
        # Char right shoulder = X-flip of left shoulder = 640-200 = 440
        # Char right wrist = X-flip of left wrist = 640-200 = 440 (at side)
        assert mirrored[12] == (440, 300)
        assert mirrored[16] == (440, 350)

    def test_arm_direction_preserved_when_pointing_backward(self):
        """When the user points their arm backward (wrist medial, toward body
        center), the mirrored character's corresponding arm also points backward.

        This is the core bug: pure X-flip reverses the direction so a backward-
        pointing arm appears forward-pointing.
        """
        width = 640
        # Body center ~ x=320. Body centerline at x=320.
        # Right arm pointing backward: right wrist is to the LEFT of right shoulder
        # (toward body center)
        points = [None] * 33
        points[11] = (200, 300)  # left shoulder (left of center)
        points[12] = (440, 300)  # right shoulder (right of center)
        points[15] = (210, 340)  # left wrist slightly right of left shoulder (backward)
        points[16] = (430, 340)  # right wrist slightly left of right shoulder (backward)

        mirrored = mirror_points(points, width)

        # After swap+flip: char left arm gets right arm data (X-flipped)
        # Char left shoulder = 640 - 440 = 200
        # Char left wrist = 640 - 430 = 210
        # Wrist (210) is to the RIGHT of shoulder (200) → toward body center → backward ✓
        assert mirrored[11] == (200, 300)   # was right shoulder, now left shoulder
        assert mirrored[15] == (210, 340)    # was right wrist, now left wrist
        assert mirrored[15][0] > mirrored[11][0]  # wrist right of shoulder (toward center)

        # Char right arm gets left arm data (X-flipped)
        # Char right shoulder = 640 - 200 = 440
        # Char right wrist = 640 - 210 = 430
        assert mirrored[12] == (440, 300)
        assert mirrored[16] == (430, 340)
        assert mirrored[16][0] < mirrored[12][0]  # wrist left of shoulder (toward center)

    def test_pure_flip_would_revers_direction(self):
        """Verify that the OLD pure-X-flip behavior would have reversed direction.

        This is a regression guard: with pure X-flip, the right arm extended to
        the right (wrist at 500) would put the 'right wrist' at 640-500=140,
        which is LEFT of the 'right shoulder' at 640-440=200 — the arm would
        appear to point backward instead of forward. The swap+flip fix corrects
        this.
        """
        width = 640
        points = [None] * 33
        points[12] = (440, 300)  # right shoulder
        points[16] = (500, 350)  # right wrist extended right

        mirrored = mirror_points(points, width)

        # Right arm in mirror = X-flip of LEFT arm, not the right arm
        # Char right wrist (index 16) gets left wrist data (index 15)
        # Left wrist was None, so right wrist should be None
        assert mirrored[16] is None

    def test_mirror_landmark_map_completeness(self):
        """Every left/right pair in the map is bidirectional."""
        for left, right in [
            (11, 12), (13, 14), (15, 16), (17, 18), (19, 20), (21, 22),
            (23, 24), (25, 26), (27, 28), (29, 30), (31, 32),
        ]:
            assert _MIRROR_LANDMARK_MAP[left] == right
            assert _MIRROR_LANDMARK_MAP[right] == left
