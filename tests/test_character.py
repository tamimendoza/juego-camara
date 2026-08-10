"""Unit tests for CharacterManager (multi-person character lifecycle and rendering)."""

import numpy as np
import pytest

from src.character import CHARACTER_COLORS, CharacterManager, MimicCharacter
from src.pose_detector import PoseResult


class FakeLandmark:
    """A minimal landmark object compatible with landmarks_to_pixels."""

    def __init__(self, x=0.5, y=0.5, visibility=1.0, presence=1.0):
        self.x = x
        self.y = y
        self.visibility = visibility
        self.presence = presence


def make_landmarks(n=33):
    """Create n FakeLandmark objects (normalized coordinates near center)."""
    return [FakeLandmark(0.5, 0.5) for _ in range(n)]


def make_pose_result(landmarks=None, success=True):
    """Create a PoseResult for testing."""
    return PoseResult(
        landmarks=landmarks if landmarks is not None else make_landmarks(),
        success=success,
    )


class TestCharacterManagerLifecycle:
    def test_no_poses_no_characters(self):
        """Updating with an empty pose list produces no characters."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update([], connections=[(11, 12)])
        assert manager.num_people == 0

    def test_one_pose_creates_one_character(self):
        """A single detected pose creates exactly one character."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update([make_pose_result()], connections=[(11, 12)])
        assert manager.num_people == 1

    def test_two_poses_create_two_characters(self):
        """Two detected poses create two characters."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update(
            [make_pose_result(), make_pose_result()],
            connections=[(11, 12)],
        )
        assert manager.num_people == 2

    def test_decreasing_poses_removes_characters(self):
        """When fewer people are detected, excess characters are removed."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update([make_pose_result(), make_pose_result()], connections=[(11, 12)])
        assert manager.num_people == 2
        manager.update([make_pose_result()], connections=[(11, 12)])
        assert manager.num_people == 1

    def test_increasing_poses_adds_characters(self):
        """When more people are detected, new characters are created."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update([make_pose_result()], connections=[(11, 12)])
        assert manager.num_people == 1
        manager.update(
            [make_pose_result(), make_pose_result()],
            connections=[(11, 12)],
        )
        assert manager.num_people == 2

    def test_zero_poses_after_detection_clears_characters(self):
        """When no people are detected, all characters are removed."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update([make_pose_result()], connections=[(11, 12)])
        assert manager.num_people == 1
        manager.update([], connections=[(11, 12)])
        assert manager.num_people == 0

    def test_new_character_inherits_current_style(self):
        """A newly created character starts with the manager's current style."""
        manager = CharacterManager(640, 480, max_persons=4)
        # Cycle to style 3
        manager.cycle_style()
        manager.cycle_style()
        manager.cycle_style()
        # Now add a person
        manager.update([make_pose_result()], connections=[(11, 12)])
        char = manager._characters[0]
        assert char._style_index == 3

    def test_new_character_inherits_mirror_mode(self):
        """A newly created character inherits the manager's mirror mode."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.toggle_mirror()  # turn mirror on
        manager.update([make_pose_result()], connections=[(11, 12)])
        char = manager._characters[0]
        assert char.mirror_mode is True


class TestCharacterManagerStyle:
    def test_cycle_style_all_characters(self):
        """cycle_style() advances the style index for all characters."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update(
            [make_pose_result(), make_pose_result()],
            connections=[(11, 12)],
        )
        idx = manager.cycle_style()
        assert idx == 1
        for char in manager._characters:
            assert char._style_index == 1

    def test_cycle_style_wraps_around(self):
        """cycle_style() wraps around to 0 after the last style."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update([make_pose_result()], connections=[(11, 12)])
        # Cycle past the end
        for _ in range(len(MimicCharacter.STYLES)):
            manager.cycle_style()
        # After cycling len(STYLES) times, we should be back at 0
        assert manager._style_index == 0

    def test_toggle_mirror_all_characters(self):
        """toggle_mirror() flips mirror mode for all characters."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update(
            [make_pose_result(), make_pose_result()],
            connections=[(11, 12)],
        )
        on = manager.toggle_mirror()
        assert on is True
        for char in manager._characters:
            assert char.mirror_mode is True

    def test_style_name_reflects_current_style(self):
        """style_name returns the name of the current style."""
        manager = CharacterManager(640, 480, max_persons=4)
        name = manager.style_name
        assert "blank" not in name  # Style 0 is mask-based
        # Cycle to style 5 (head_circle)
        for _ in range(5):
            manager.cycle_style()
        assert "head_circle" in manager.style_name

    def test_style_name_no_characters(self):
        """style_name works even when no characters exist."""
        manager = CharacterManager(640, 480, max_persons=4)
        assert manager.style_name is not None


class TestCharacterManagerRender:
    def test_render_multiple_characters_distinct_colors(self):
        """Each character uses a distinct color from the palette."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update(
            [make_pose_result(), make_pose_result(), make_pose_result()],
            connections=[(11, 12)],
        )
        # Character 0 uses white, char 1 uses red, char 2 uses green
        assert manager._characters[0]._drawer.joint_color == CHARACTER_COLORS[0]
        assert manager._characters[1]._drawer.joint_color == CHARACTER_COLORS[1]
        assert manager._characters[2]._drawer.joint_color == CHARACTER_COLORS[2]

    def test_render_does_not_crash_with_no_characters(self):
        """Rendering with no characters is a no-op."""
        manager = CharacterManager(640, 480, max_persons=4)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        manager.render(frame)
        # Frame should still be all black
        assert frame.sum() == 0

    def test_render_draws_each_character(self):
        """Rendering two characters draws content from both."""
        manager = CharacterManager(640, 480, max_persons=4)
        manager.update(
            [make_pose_result(), make_pose_result()],
            connections=[(11, 12)],
        )
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        manager.render(frame)
        # At least one pixel should be non-zero (both characters share center)
        assert frame.sum() > 0

    def test_color_wraps_for_more_than_palette_size(self):
        """Characters beyond palette size reuse colors from the start."""
        manager = CharacterManager(640, 480, max_persons=6)
        manager.update(
            [make_pose_result() for _ in range(6)],
            connections=[(11, 12)],
        )
        # Character 4 should reuse color_index 0
        assert manager._characters[4]._drawer.joint_color == CHARACTER_COLORS[0]
        # Character 5 should reuse color_index 1
        assert manager._characters[5]._drawer.joint_color == CHARACTER_COLORS[1]

    def test_render_styles_both_characters_visible(self):
        """With 'blank' style, both characters are visible — background applied once."""
        manager = CharacterManager(640, 480, max_persons=4)
        connections = [(11, 13), (12, 14)]
        lms1 = [FakeLandmark(0.3, 0.3) for _ in range(33)]
        lms2 = [FakeLandmark(0.7, 0.7) for _ in range(33)]
        results1 = [PoseResult(landmarks=lms1, success=True)]
        results2 = [PoseResult(landmarks=lms2, success=True)]
        manager.update(results1 + results2, connections=connections)

        # Cycle to Style 5 (5 presses)
        for _ in range(5):
            manager.cycle_style()
        assert manager.style_name == "blank, head_circle, body_lines"

        frame = np.full((480, 640, 3), 255, dtype=np.uint8)
        manager.render(frame)

        # Background should be black (blank applied once)
        assert frame[0, 0, 0] == 0

        # Both character centers should have their respective colors
        p1 = frame[144, 192]  # person 0 at (0.3*640, 0.3*480) = (192, 144)
        p2 = frame[336, 448]  # person 1 at (0.7*640, 0.7*480) = (448, 336)
        assert p1[0] == 255, "Person 0 (white) not rendered"
        assert p2[2] == 255 and p2[0] == 0, "Person 1 (red) not rendered"
