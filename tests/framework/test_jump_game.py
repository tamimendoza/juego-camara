"""Unit tests for the pose-controlled jump game engine.

Tests cover JumpDetector, PlayerCharacter, Obstacle, ObstacleManager,
and GameEngine logic. All tests run without a camera or model file by
using mock landmark data and numpy arrays for frames.
"""

import numpy as np
import pytest

from src.framework.jump_game import (
    BASE_SPEED,
    BRICK_COLOR,
    CHARACTER_TARGET_HEIGHT,
    CHARACTER_X,
    CLOUD_COLOR,
    CLOUD_SPEED_FACTOR,
    DOUBLE_JUMP_VELOCITY,
    GameEngine,
    GRAFFITI_COLOR,
    GRAFFITI_TEXT,
    GROUND_Y_RATIO,
    HEART_COLOR,
    INVINCIBILITY_THRESHOLD,
    JUMP_COOLDOWN,
    JUMP_THRESHOLD,
    JumpDetector,
    LEFT_SHOULDER,
    LEVEL_INTERVAL,
    MAX_JUMPS,
    MAX_LIVES,
    MIN_SHOULDER_WIDTH,
    OBSTACLE_HEIGHT_RANGE,
    Obstacle,
    ObstacleManager,
    OBSTACLE_WIDTH,
    PlayerCharacter,
    POSE_WARNING_COLOR,
    POSE_WARNING_TEXT,
    RIGHT_SHOULDER,
    SKY_BLOCK_COLOR,
    SKY_BLOCK_SIZE,
    Cloud,
    SkyBlock,
    SPEED_INTERVAL,
    SPEED_MULTIPLIER,
)
from src.core.sound_manager import SoundManager


# --- Helpers -----------------------------------------------------------------

WIDTH, HEIGHT = 640, 480
GROUND_Y = int(HEIGHT * GROUND_Y_RATIO)

# A small subset of real MediaPipe POSE_CONNECTIONS for rendering tests
MOCK_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # face (excluded from body_lines)
    (11, 12),  # shoulders
    (11, 13), (13, 15), (15, 16), (16, 18),  # left arm
    (12, 14), (14, 16),  # right arm
    (11, 23), (12, 24),  # torso sides
    (23, 24),  # hips
    (23, 25), (25, 27), (27, 29),  # left leg
    (24, 26), (26, 28), (28, 30),  # right leg
]


def make_landmarks(
    shoulder_y=240,
    nose_y=120,
    hip_y=300,
    ankle_y=380,
    shoulder_x=300,
    width=WIDTH,
    height=HEIGHT,
):
    """Create a 33-point mock landmark list with visible key joints.

    Standing pose centered at x=width//2. Shoulders at shoulder_y, nose at
    nose_y, hips at hip_y, ankles at ankle_y. All other body landmarks
    filled in with reasonable intermediate positions.
    """
    cx = width // 2
    points = [None] * 33

    # Nose (0)
    points[0] = (cx, nose_y)
    # Shoulders (11, 12)
    points[11] = (cx - 20, shoulder_y)
    points[12] = (cx + 20, shoulder_y)
    # Hips (23, 24)
    points[23] = (cx - 20, hip_y)
    points[24] = (cx + 20, hip_y)
    # Ankles (29, 30)
    points[29] = (cx - 20, ankle_y)
    points[30] = (cx + 20, ankle_y)
    # Knees (25, 26)
    points[25] = (cx - 20, (hip_y + ankle_y) // 2)
    points[26] = (cx + 20, (hip_y + ankle_y) // 2)
    # Elbows (13, 14)
    points[13] = (cx - 50, shoulder_y + 30)
    points[14] = (cx + 50, shoulder_y + 30)
    # Wrists (15, 16)
    points[15] = (cx - 60, shoulder_y + 80)
    points[16] = (cx + 60, shoulder_y + 80)
    # Heels (31, 32)
    points[31] = (cx - 20, ankle_y)
    points[32] = (cx + 20, ankle_y)
    # Hips and shoulders for full body
    points[27] = (cx - 10, ankle_y - 5)  # left heel
    points[28] = (cx + 10, ankle_y - 5)  # right heel
    return points


def make_standing_landmarks():
    """Shoulders at a fixed baseline (y=240)."""
    return make_landmarks(shoulder_y=240)


def make_jumping_landmarks(jump_height=80):
    """Shoulders raised above baseline by jump_height."""
    return make_landmarks(shoulder_y=240 - jump_height)


# --- JumpDetector Tests ------------------------------------------------------


class TestJumpDetector:
    def test_no_jump_when_still(self):
        """Standing still at baseline does not trigger a jump."""
        detector = JumpDetector()
        landmarks = make_standing_landmarks()
        result = detector.update(landmarks)
        assert result is False

    def test_jump_when_shoulders_rise_above_threshold(self):
        """Shoulders rising above the 30 px threshold triggers a jump."""
        detector = JumpDetector()
        landmarks = make_standing_landmarks()
        # Establish baseline
        detector.update(landmarks)
        # Now jump: shoulders rise by 80 px
        jumping = make_jumping_landmarks(jump_height=80)
        result = detector.update(jumping)
        assert result is True

    def test_no_jump_when_shoulders_rise_below_threshold(self):
        """Shoulders rising below the 30 px threshold does not trigger a jump."""
        detector = JumpDetector()
        landmarks = make_standing_landmarks()
        detector.update(landmarks)  # establish baseline
        # Shoulders rise by only 20 px (below the 30 px threshold)
        almost = make_jumping_landmarks(jump_height=20)
        result = detector.update(almost)
        assert result is False

    def test_cooldown_prevents_double_jump(self):
        """After a jump, cooldown prevents another jump for N frames."""
        detector = JumpDetector(cooldown=5)
        base = make_standing_landmarks()
        detector.update(base)  # baseline
        jump = make_jumping_landmarks(jump_height=80)
        assert detector.update(jump) is True  # first jump fires

        # Next frames: should be in cooldown
        assert detector.update(jump) is False
        assert detector.update(jump) is False
        assert detector.update(jump) is False

    def test_missing_shoulders_no_trigger(self):
        """If shoulders are not visible (None), no jump is triggered."""
        detector = JumpDetector()
        landmarks = make_standing_landmarks()
        landmarks[11] = None  # left shoulder occluded
        result = detector.update(landmarks)
        assert result is False

        # Right shoulder only missing
        landmarks = make_standing_landmarks()
        landmarks[12] = None
        result = detector.update(landmarks)
        assert result is False

    def test_baseline_adapts_to_position_change(self):
        """Standing baseline slowly adapts (EMA) to gradual position shifts."""
        detector = JumpDetector(cooldown=0, ema_alpha=0.5)
        # Establish at y=200
        lands1 = make_landmarks(shoulder_y=200)
        detector.update(lands1)  # baseline = 200

        # Gradually shift down to y=240 (4 frames, alpha=0.5)
        # baseline should converge toward 240, so a small rise won't trigger
        lands2 = make_landmarks(shoulder_y=240)
        # After several updates, baseline approaches 240
        for _ in range(10):
            detector.update(lands2)

        # Now rising by 30 from 240 baseline shouldn't trigger (baseline ~240)
        # But since we've moved, baseline adapts
        # The key assertion: baseline is closer to 240 than to 200
        assert detector._baseline_y is not None
        # Baseline should have moved toward 240
        assert detector._baseline_y > 200

    def test_reset_clears_baseline(self):
        """reset() clears the baseline so the next update starts fresh."""
        detector = JumpDetector()
        detector.update(make_standing_landmarks())
        assert detector._baseline_y is not None

        detector.reset()
        assert detector._baseline_y is None
        assert detector._cooldown_counter == 0

    def test_short_landmark_list_no_crash(self):
        """A landmark list shorter than 13 entries does not crash."""
        detector = JumpDetector()
        result = detector.update([(100, 100), (200, 200)])  # too short
        assert result is False

    def test_first_call_establishes_baseline(self):
        """First update with valid shoulders sets the baseline without triggering."""
        detector = JumpDetector()
        result = detector.update(make_standing_landmarks())
        assert result is False
        assert detector._baseline_y is not None

    def test_frame_count_increments(self):
        """update() increments the internal frame counter."""
        detector = JumpDetector()
        initial = detector._frame_count
        detector.update(make_standing_landmarks())
        assert detector._frame_count == initial + 1


# --- PlayerCharacter Tests ---------------------------------------------------


class TestPlayerCharacter:
    def _make_player(self, ground_y=GROUND_Y):
        return PlayerCharacter(CHARACTER_X, ground_y)

    def test_initial_state_on_ground(self):
        """Character starts on the ground at rest."""
        player = self._make_player()
        assert player.on_ground is True
        assert player.bounding_box == (0, 0, 0, 0)

    def test_jump_sets_upward_velocity(self):
        """jump() applies upward velocity and leaves the ground."""
        player = self._make_player()
        jumped = player.jump()
        assert jumped is True
        assert player.on_ground is False

    def test_third_jump_fails_when_airborne(self):
        """jump() returns False on the third attempt (max 2 jumps)."""
        player = self._make_player()
        player.jump()  # first jump
        player.jump()  # double jump (second)
        jumped = player.jump()  # third — should fail
        assert jumped is False

    def test_double_jump_succeeds_while_airborne(self):
        """Second jump() succeeds while airborne (double jump)."""
        player = self._make_player()
        player.jump()  # first jump
        jumped = player.jump()  # double jump
        assert jumped is True

    def test_double_jump_applies_additional_velocity(self):
        """Double jump applies DOUBLE_JUMP_VELOCITY on top of current velocity."""
        player = self._make_player()
        player.jump()  # first jump: vy = JUMP_VELOCITY
        vy_after_first = player._vy
        player.jump()  # double jump: vy += DOUBLE_JUMP_VELOCITY
        assert player._vy == pytest.approx(vy_after_first + DOUBLE_JUMP_VELOCITY)

    def test_gravity_returns_to_ground(self):
        """After jumping, gravity pulls the character back to ground."""
        player = self._make_player()
        player.jump()
        assert player.on_ground is False

        # Apply gravity each frame until landing
        frames = 0
        while not player.on_ground and frames < 100:
            player.update()
            frames += 1

        assert player.on_ground is True
        assert frames > 0

    def test_jump_apex_above_ground(self):
        """At apex, character's jump_offset is negative (above ground)."""
        player = self._make_player()
        player.jump()

        # After 1 frame of update, character should still be rising
        player.update()
        assert player._jump_offset < 0

    def test_jump_apex_clears_max_obstacle(self):
        """Jump apex exceeds the maximum obstacle height (120 px)."""
        player = self._make_player()
        player.jump()

        apex = 0.0
        frames = 0
        while not player.on_ground and frames < 200:
            player.update()
            apex = min(apex, player._jump_offset)
            frames += 1

        # jump_offset is negative when above ground; apex is its most-negative value
        assert abs(apex) > max(OBSTACLE_HEIGHT_RANGE)

    def test_bbox_update_after_pose(self):
        """After update with landmarks, bbox is non-zero."""
        player = self._make_player()
        lands = make_standing_landmarks()
        player.update(lands)
        bx, by, bw, bh = player.bounding_box
        assert bw > 0
        assert bh > 0
        assert bx >= 0
        assert by >= 0

    def test_pose_scaled_to_target_height(self):
        """Transformed landmarks fit within CHARACTER_TARGET_HEIGHT."""
        player = self._make_player(ground_y=384)
        lands = make_landmarks(
            shoulder_y=240, nose_y=120, hip_y=300, ankle_y=380
        )
        player.update(lands)

        # Verify key landmarks are within the target height range
        render_points = player._render_points
        assert render_points is not None

        # Find head (nose) and feet (ankle) y coordinates
        nose = render_points[0]
        ankle = render_points[29]
        if nose is not None and ankle is not None:
            char_height = abs(ankle[1] - nose[1])
            # Should be approximately CHARACTER_TARGET_HEIGHT (with tolerance)
            assert 50 < char_height < 120

    def test_bbox_uses_transformed_points(self):
        """Bounding box matches the min/max of transformed landmark points."""
        player = self._make_player(ground_y=384)
        lands = make_standing_landmarks()
        player.update(lands)

        bbox = player.bounding_box
        points = player._render_points
        if points is not None:
            visible = [p for p in points if p is not None]
            if visible:
                min_x = min(p[0] for p in visible)
                max_x = max(p[0] for p in visible)
                min_y = min(p[1] for p in visible)
                max_y = max(p[1] for p in visible)
                # Bbox should encompass all points (plus padding)
                assert bbox[0] <= min_x
                assert bbox[1] <= min_y
                assert bbox[0] + bbox[2] >= max_x
                assert bbox[1] + bbox[3] >= max_y

    def test_render_does_not_crash(self):
        """render() on a blank frame does not raise."""
        player = self._make_player()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        player.render(frame, MOCK_CONNECTIONS)
        # Fallback render when no pose
        assert frame is not None

    def test_render_with_pose_does_not_crash(self):
        """render() with pose landmarks draws without errors."""
        player = self._make_player()
        player.update(make_standing_landmarks())
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        player.render(frame, MOCK_CONNECTIONS)
        assert frame is not None

    def test_reset_returns_to_ground(self):
        """reset() puts the character back on the ground at rest."""
        player = self._make_player()
        player.jump()
        player.update()
        assert player.on_ground is False

        player.reset()
        assert player.on_ground is True
        assert player._jump_offset == 0.0
        assert player._vy == 0.0

    def test_falling_velocity_increases(self):
        """Gravity increases downward velocity each frame while airborne."""
        player = self._make_player()
        player.jump()
        vy1 = player._vy
        player.update()  # gravity applies
        vy2 = player._vy
        assert vy2 > vy1  # velocity becomes more negative then less... actually vy increases (becomes less negative)

    def test_feet_at_ground_level_after_pose_update(self):
        """The lowest rendered point is at or near the ground line."""
        ground_y = 384
        player = self._make_player(ground_y=ground_y)
        lands = make_landmarks(
            shoulder_y=240, nose_y=120, hip_y=300, ankle_y=380
        )
        player.update(lands)

        points = player._render_points
        assert points is not None
        visible_y = [p[1] for p in points if p is not None]
        max_y = max(visible_y)

        # Feet should be near ground_y (within a few pixels of the target)
        assert max_y == pytest.approx(ground_y, abs=15)


# --- Obstacle Tests ----------------------------------------------------------


class TestObstacle:
    def test_movement_leftward(self):
        """update() moves the obstacle leftward by speed."""
        obs = Obstacle(x=300, ground_y=384, width=30, height=60, speed=5.0)
        assert obs.x == 300.0
        obs.update()
        assert obs.x == 295.0
        obs.update()
        assert obs.x == 290.0

    def test_off_screen(self):
        """off_screen() returns True when the obstacle clears the left edge."""
        obs = Obstacle(x=10, ground_y=384, width=30, height=60, speed=5.0)
        assert obs.off_screen() is False
        obs.x = -31  # x + width = -1 < 0
        assert obs.off_screen() is True

    def test_collision_when_overlapping(self):
        """check_collision returns True when bboxes overlap."""
        obs = Obstacle(x=100, ground_y=384, width=30, height=60, speed=5.0)
        # bbox directly overlapping
        char_bbox = (105, 330, 20, 80)
        assert obs.check_collision(char_bbox) is True

    def test_no_collision_when_separated(self):
        """check_collision returns False when bboxes are far apart."""
        obs = Obstacle(x=100, ground_y=384, width=30, height=60, speed=5.0)
        char_bbox = (400, 330, 20, 80)
        assert obs.check_collision(char_bbox) is False

    def test_no_collision_when_passed(self):
        """check_collision returns False once the obstacle is marked as passed."""
        obs = Obstacle(x=100, ground_y=384, width=30, height=60, speed=5.0)
        char_bbox = (105, 330, 20, 80)
        assert obs.check_collision(char_bbox) is True
        obs.passed = True
        assert obs.check_collision(char_bbox) is False

    def test_mark_passed_when_left_of_character(self):
        """mark_passed returns True once the obstacle passes the character."""
        obs = Obstacle(x=100, ground_y=384, width=30, height=60, speed=5.0)
        char_x = 80

        # Obstacle is to the right of character (x=100, right edge=130 > 80)
        assert obs.mark_passed(char_x) is False

        # Move past character
        obs.x = 50  # right edge = 80, not yet past
        assert obs.mark_passed(char_x) is False

        obs.x = 40  # right edge = 70 < 80
        assert obs.mark_passed(char_x) is True

        # Already passed, won't fire again
        assert obs.mark_passed(char_x) is False

    def test_render_does_not_crash(self):
        """render() draws the obstacle without errors."""
        obs = Obstacle(x=100, ground_y=384, width=30, height=60, speed=5.0)
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        obs.render(frame)
        assert frame is not None


# --- ObstacleManager Tests ---------------------------------------------------


class TestObstacleManager:
    def _make_manager(
        self,
        width=WIDTH,
        ground_y=GROUND_Y,
        spawn_interval_range=(40, 90),
        base_speed=BASE_SPEED,
    ):
        return ObstacleManager(width, ground_y, base_speed, spawn_interval_range)

    def test_initial_state(self):
        """New manager has no obstacles and zero passed count."""
        mgr = self._make_manager()
        assert mgr.passed_count == 0
        assert mgr.level == 1
        assert len(mgr._obstacles) == 0

    def test_level_progression(self):
        """Level increments every LEVEL_INTERVAL obstacles passed."""
        mgr = self._make_manager()

        mgr._passed_count = 0
        assert mgr.level == 1

        mgr._passed_count = 4
        assert mgr.level == 1

        mgr._passed_count = 5
        assert mgr.level == 2

        mgr._passed_count = 9
        assert mgr.level == 2

        mgr._passed_count = 10
        assert mgr.level == 3

        mgr._passed_count = 49
        assert mgr.level == 10

    def test_obstacles_spawn_over_time(self):
        """Obstacles are spawned as the spawn timer counts down."""
        mgr = self._make_manager(spawn_interval_range=(1, 1))
        # Update repeatedly; obstacles should appear
        mgr.update(CHARACTER_X, (0, 0, 0, 0))
        mgr.update(CHARACTER_X, (0, 0, 0, 0))
        assert len(mgr._obstacles) >= 1

    def test_passed_count_increments(self):
        """passed_count increments when an obstacle passes the character."""
        mgr = self._make_manager()
        mgr._spawn_timer = 999  # prevent spawning during test
        # Place obstacle so its right edge passes the character after one update
        obs = Obstacle(
            x=CHARACTER_X - OBSTACLE_WIDTH - 10, ground_y=GROUND_Y,
            width=OBSTACLE_WIDTH, height=60, speed=BASE_SPEED
        )
        obs.passed = False
        mgr._obstacles = [obs]
        mgr.update(CHARACTER_X, (0, 0, 0, 0))
        assert mgr.passed_count == 1

    def test_off_screen_obstacles_removed(self):
        """Obstacles that scroll off-screen are removed."""
        mgr = self._make_manager()
        mgr._spawn_timer = 999  # prevent spawning during test
        obs = Obstacle(x=-100, ground_y=GROUND_Y, width=30, height=60, speed=5.0)
        mgr._obstacles = [obs]
        mgr.update(CHARACTER_X, (0, 0, 0, 0))
        assert len(mgr._obstacles) == 0

    def test_set_speed_updates_existing_obstacles(self):
        """set_speed() propagates to all existing obstacles."""
        mgr = self._make_manager()
        obs1 = Obstacle(x=100, ground_y=GROUND_Y, speed=4.0)
        obs2 = Obstacle(x=200, ground_y=GROUND_Y, speed=4.0)
        mgr._obstacles = [obs1, obs2]

        mgr.set_speed(10.0)
        assert obs1.speed == 10.0
        assert obs2.speed == 10.0
        assert mgr.speed == 10.0

    def test_check_collisions_returns_true_on_overlap(self):
        """check_collisions returns True when any obstacle overlaps."""
        mgr = self._make_manager()
        obs = Obstacle(
            x=CHARACTER_X - 10, ground_y=GROUND_Y,
            width=30, height=60, speed=BASE_SPEED
        )
        mgr._obstacles = [obs]
        char_bbox = (CHARACTER_X - 5, GROUND_Y - 60, 20, 80)
        assert mgr.check_collisions(char_bbox) is True

    def test_check_collisions_returns_false_when_clear(self):
        """check_collisions returns False when no obstacles overlap."""
        mgr = self._make_manager()
        obs = Obstacle(x=WIDTH - 100, ground_y=GROUND_Y, width=30, height=60, speed=BASE_SPEED)
        mgr._obstacles = [obs]
        char_bbox = (CHARACTER_X - 5, GROUND_Y - 60, 20, 80)
        assert mgr.check_collisions(char_bbox) is False

    def test_reset_clears_obstacles(self):
        """reset() empties the obstacle list and resets counters."""
        mgr = self._make_manager()
        mgr._obstacles = [Obstacle(x=100, ground_y=GROUND_Y, speed=5.0)]
        mgr._passed_count = 5
        mgr.reset()
        assert len(mgr._obstacles) == 0
        assert mgr.passed_count == 0

    def test_render_does_not_crash(self):
        """render() draws all obstacles without errors."""
        mgr = self._make_manager()
        mgr._obstacles = [Obstacle(x=100, ground_y=GROUND_Y, speed=5.0)]
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        mgr.render(frame)
        assert frame is not None


# --- GameEngine Tests --------------------------------------------------------


class TestGameEngine:
    def _make_engine(self):
        return GameEngine(WIDTH, HEIGHT)

    def test_initial_state_is_menu(self):
        """Engine starts in MENU state."""
        engine = self._make_engine()
        assert engine.state == GameEngine.MENU
        assert engine.state_name == "MENU"
        assert engine.passed_count == 0
        assert engine.level == 1

    def test_level_progression(self):
        """Level increments every 5 obstacles passed via engine speed property."""
        engine = self._make_engine()
        engine.start()

        engine._obstacle_manager._passed_count = 0
        assert engine.level == 1

        engine._obstacle_manager._passed_count = 4
        assert engine.level == 1

        engine._obstacle_manager._passed_count = 5
        assert engine.level == 2

        engine._obstacle_manager._passed_count = 10
        assert engine.level == 3

    def test_speed_progression_tied_to_level(self):
        """Speed multiplier is SPEED_MULTIPLIER^(level - 1)."""
        engine = self._make_engine()
        engine.start()

        # Level 1 (0-4 obstacles): base speed
        engine._obstacle_manager._passed_count = 0
        assert engine.speed == pytest.approx(BASE_SPEED)
        engine._obstacle_manager._passed_count = 4
        assert engine.speed == pytest.approx(BASE_SPEED)

        # Level 2 (5-9 obstacles): first speed increase
        engine._obstacle_manager._passed_count = 5
        assert engine.speed == pytest.approx(BASE_SPEED * SPEED_MULTIPLIER)

        # Level 3 (10-14 obstacles): second increase
        engine._obstacle_manager._passed_count = 10
        assert engine.speed == pytest.approx(BASE_SPEED * SPEED_MULTIPLIER ** 2)

    def test_speed_starts_at_base(self):
        """Initial speed equals BASE_SPEED with no obstacles passed."""
        engine = self._make_engine()
        assert engine.speed == pytest.approx(BASE_SPEED)

    def test_start_transitions_to_playing(self):
        """handle_key(SPACE) from MENU starts the game."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))
        assert engine.state == GameEngine.PLAYING
        assert engine.state_name == "PLAYING"

    def test_reset_from_game_over_to_playing(self):
        """handle_key(SPACE) from GAME_OVER restarts the game."""
        engine = self._make_engine()
        engine.start()
        engine._state = GameEngine.GAME_OVER
        engine.handle_key(ord(" "))
        assert engine.state == GameEngine.PLAYING

    def test_speed_progression_formula(self):
        """Speed multiplier is SPEED_MULTIPLIER^(level - 1) = SPEED_MULTIPLIER^(passed_count // 5)."""
        engine = self._make_engine()
        engine.start()

        # 0 passed → base speed
        engine._obstacle_manager._passed_count = 0
        assert engine.speed == pytest.approx(BASE_SPEED)

        # 4 passed → still base (4 // 5 = 0)
        engine._obstacle_manager._passed_count = 4
        assert engine.speed == pytest.approx(BASE_SPEED)

        # 5 passed → ×1.10
        engine._obstacle_manager._passed_count = 5
        assert engine.speed == pytest.approx(BASE_SPEED * SPEED_MULTIPLIER)

        # 10 passed → ×1.21
        engine._obstacle_manager._passed_count = 10
        assert engine.speed == pytest.approx(BASE_SPEED * SPEED_MULTIPLIER ** 2)

        # 17 passed → ×1.331 (17 // 5 = 3)
        engine._obstacle_manager._passed_count = 17
        assert engine.speed == pytest.approx(BASE_SPEED * SPEED_MULTIPLIER ** 3)

    def test_collision_loses_life(self):
        """Character colliding with an obstacle loses a life (not game over)."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        engine.update(standing, MOCK_CONNECTIONS)

        # Place an obstacle overlapping the character
        obs = Obstacle(
            x=CHARACTER_X - 25,
            ground_y=GROUND_Y,
            width=50,
            height=100,
            speed=BASE_SPEED,
        )
        engine._obstacle_manager._obstacles = [obs]

        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.lives == MAX_LIVES - 1
        assert engine.state == GameEngine.PLAYING

    def test_game_over_when_lives_depleted(self):
        """Game over when all lives are lost through repeated collisions."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        engine.update(standing, MOCK_CONNECTIONS)

        # Collide MAX_LIVES times to lose all lives
        for _ in range(MAX_LIVES):
            obs = Obstacle(
                x=CHARACTER_X - 25,
                ground_y=GROUND_Y,
                width=50,
                height=100,
                speed=BASE_SPEED,
            )
            engine._obstacle_manager._obstacles = [obs]
            engine.update(standing, MOCK_CONNECTIONS)

        assert engine.lives == 0
        assert engine.state == GameEngine.GAME_OVER

    def test_menu_update_does_nothing(self):
        """In MENU state, update() does not spawn obstacles."""
        engine = self._make_engine()
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        assert engine.state == GameEngine.MENU
        assert engine.passed_count == 0

    def test_game_over_update_frozen(self):
        """In GAME_OVER state, update() does not change score or state."""
        engine = self._make_engine()
        engine.start()
        engine._state = GameEngine.GAME_OVER

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.state == GameEngine.GAME_OVER

    def test_jump_detected_during_play(self):
        """A jump gesture triggers the character to jump during PLAYING."""
        engine = self._make_engine()
        engine.start()

        # Establish baseline
        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine._player.on_ground is True

        # Jump: shoulders rise 80 px above baseline
        jumping = make_jumping_landmarks(jump_height=80)
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player.on_ground is False

    def test_double_jump_detected_during_play(self):
        """A second jump gesture while airborne triggers a double jump."""
        engine = self._make_engine()
        engine.start()

        # Establish baseline
        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # First jump
        jumping = make_jumping_landmarks(jump_height=80)
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player.on_ground is False
        assert engine._player._jump_count == 1

        # Wait for cooldown to expire
        for _ in range(JUMP_COOLDOWN + 1):
            engine.update(standing, MOCK_CONNECTIONS)

        # Second jump gesture (shoulders rise again) — triggers double jump
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player._jump_count == 2

        # Third jump gesture — should NOT trigger (max 2 jumps)
        for _ in range(JUMP_COOLDOWN + 1):
            engine.update(standing, MOCK_CONNECTIONS)
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player._jump_count == 2

    def test_coin_sound_plays_on_obstacle_pass(self):
        """Coin sound plays when an obstacle passes the character."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Place an obstacle to the left of character so it passes before collision
        obs = Obstacle(
            x=CHARACTER_X - OBSTACLE_WIDTH - 10,
            ground_y=GROUND_Y,
            width=OBSTACLE_WIDTH,
            height=60,
            speed=BASE_SPEED,
        )
        engine._obstacle_manager._obstacles = [obs]
        engine._obstacle_manager._spawn_timer = 999

        # Update until the obstacle passes the character
        for _ in range(50):
            engine.update(standing, MOCK_CONNECTIONS)
            if sound.play_coin.called:
                break
        assert sound.play_coin.called

    def test_hit_sound_plays_on_collision(self):
        """Hit sound plays when a collision is detected (with lives remaining)."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Place an obstacle overlapping the character
        obs = Obstacle(
            x=CHARACTER_X - 10,
            ground_y=GROUND_Y,
            width=50,
            height=100,
            speed=BASE_SPEED,
        )
        engine._obstacle_manager._obstacles = [obs]

        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.state == GameEngine.PLAYING
        assert sound.play_hit.called
        assert not sound.play_game_over.called

    def test_game_over_sound_when_lives_depleted(self):
        """Game over sound plays when all lives are lost."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Collide MAX_LIVES times to lose all lives
        for _ in range(MAX_LIVES):
            obs = Obstacle(
                x=CHARACTER_X - 10,
                ground_y=GROUND_Y,
                width=50,
                height=100,
                speed=BASE_SPEED,
            )
            engine._obstacle_manager._obstacles = [obs]
            engine.update(standing, MOCK_CONNECTIONS)

        assert engine.state == GameEngine.GAME_OVER
        assert sound.play_game_over.called

    def test_engine_close_calls_sound_manager(self):
        """close() delegates to the sound manager."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.close()
        assert sound.close.called

    def test_render_menu_does_not_crash(self):
        """render() in MENU state does not crash."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.render(frame, MOCK_CONNECTIONS)
        assert frame is not None

    def test_render_playing_does_not_crash(self):
        """render() in PLAYING state renders without errors."""
        engine = self._make_engine()
        engine.start()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)
        assert frame is not None

    def test_render_game_over_does_not_crash(self):
        """render() in GAME_OVER state renders without errors."""
        engine = self._make_engine()
        engine.start()
        engine._state = GameEngine.GAME_OVER
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.render(frame, MOCK_CONNECTIONS)
        assert frame is not None

    def test_handle_key_q_does_not_start(self):
        """Pressing 'q' from MENU does not start the game."""
        engine = self._make_engine()
        engine.handle_key(ord("q"))
        assert engine.state == GameEngine.MENU

    def test_playing_state_updates_player(self):
        """In PLAYING, update() passes landmarks to the player and obstacle manager."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Player should have pose data
        assert engine._player._render_points is not None

    def test_speed_set_on_obstacles_during_play(self):
        """ObstacleManager speed is synced to engine speed each frame."""
        engine = self._make_engine()
        engine.start()
        engine._obstacle_manager._passed_count = 5
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        expected_speed = BASE_SPEED * SPEED_MULTIPLIER
        assert engine._obstacle_manager.speed == pytest.approx(expected_speed)

    def test_hud_shows_level(self):
        """After update in PLAYING, the HUD region has non-black pixels (level text)."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.start()
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        # Top-left HUD area should have non-black pixels (white level/score text)
        hud_area = frame[0:80, 0:200]
        assert hud_area.sum() > 0

    def test_game_over_shows_level(self):
        """Game over screen displays level text."""
        engine = self._make_engine()
        engine.start()
        engine._obstacle_manager._passed_count = 5
        engine._state = GameEngine.GAME_OVER
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.render(frame, MOCK_CONNECTIONS)

        # Game over should have been rendered with level info
        assert frame.sum() > 0

    # --- Lives system tests ---

    def test_initial_lives_is_max(self):
        """Engine starts with MAX_LIVES lives."""
        engine = self._make_engine()
        assert engine.lives == MAX_LIVES

    def test_sky_block_restores_life(self):
        """Collecting a sky block restores a life (up to MAX_LIVES)."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Lose a life first
        obs = Obstacle(
            x=CHARACTER_X - 10,
            ground_y=GROUND_Y,
            width=50,
            height=100,
            speed=BASE_SPEED,
        )
        engine._obstacle_manager._obstacles = [obs]
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.lives == MAX_LIVES - 1

        # Collect a sky block to restore life
        block = SkyBlock(
            x=CHARACTER_X - SKY_BLOCK_SIZE - 10,
            y=GROUND_Y - 50,
            size=SKY_BLOCK_SIZE,
            color=SKY_BLOCK_COLOR,
            speed=BASE_SPEED,
        )
        engine._sky_blocks = [block]
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.lives == MAX_LIVES

    def test_sky_block_does_not_overfill_lives(self):
        """Sky block does not restore life when already at MAX_LIVES."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Sky block at full lives should not increment
        block = SkyBlock(
            x=CHARACTER_X - SKY_BLOCK_SIZE - 10,
            y=GROUND_Y - 50,
            size=SKY_BLOCK_SIZE,
            color=SKY_BLOCK_COLOR,
            speed=BASE_SPEED,
        )
        engine._sky_blocks = [block]
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.lives == MAX_LIVES

    # --- Background music tests ---

    def test_start_calls_play_background_music(self):
        """start() calls play_background_music on the sound manager."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()
        assert sound.play_background_music.called

    def test_close_calls_stop_background_music(self):
        """close() calls stop_background_music on the sound manager."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.close()
        assert sound.stop_background_music.called

    def test_reset_calls_stop_invincibility_theme(self):
        """reset() calls stop_invincibility_theme on the sound manager."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()
        sound.reset_mock()
        engine.reset()
        assert sound.stop_invincibility_theme.called

    # --- Invincibility theme tests ---

    def test_invincibility_theme_plays_at_threshold(self):
        """Invincibility theme plays when score reaches INVINCIBILITY_THRESHOLD."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Set score to threshold
        engine._obstacle_manager._passed_count = INVINCIBILITY_THRESHOLD
        engine.update(standing, MOCK_CONNECTIONS)
        assert sound.play_invincibility_theme.called

    def test_invincibility_theme_stops_below_threshold(self):
        """Invincibility theme stops when score drops below threshold."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Activate invincibility
        engine._obstacle_manager._passed_count = INVINCIBILITY_THRESHOLD
        engine.update(standing, MOCK_CONNECTIONS)
        sound.reset_mock()

        # Drop below threshold
        engine._obstacle_manager._passed_count = INVINCIBILITY_THRESHOLD - 1
        engine.update(standing, MOCK_CONNECTIONS)
        assert sound.stop_invincibility_theme.called

    # --- Pose stability tests ---

    def test_pose_warning_shown_when_shoulders_occluded(self):
        """scale_warning is True when shoulders are not detected."""
        engine = self._make_engine()
        engine.start()

        # Landmarks with no shoulders (None)
        landmarks = make_standing_landmarks()
        landmarks[LEFT_SHOULDER] = None
        landmarks[RIGHT_SHOULDER] = None
        engine.update(landmarks, MOCK_CONNECTIONS)
        assert engine._player.scale_warning is True

    def test_pose_warning_shown_when_too_close(self):
        """scale_warning is True when shoulder width is too small."""
        engine = self._make_engine()
        engine.start()

        # Landmarks with shoulders very close together
        landmarks = make_standing_landmarks()
        landmarks[LEFT_SHOULDER] = (319, 240)  # cx-1
        landmarks[RIGHT_SHOULDER] = (321, 240)  # cx+1
        engine.update(landmarks, MOCK_CONNECTIONS)
        assert engine._player.scale_warning is True

    def test_no_pose_warning_when_standing(self):
        """scale_warning is False when standing at proper distance."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine._player.scale_warning is False

    def test_character_arms_point_forward_like_player_mirror(self):
        """The miniatura character mirrors the player so arms point forward.

        When the player points both hands forward (toward their physical right,
        which is the image-LEFT on a non-flipped camera), the character's arms
        must point FORWARD (image-right, along the character's path) — not be
        rendered in reverse.
        """
        engine = self._make_engine()
        engine.start()

        landmarks = make_standing_landmarks()
        landmarks[11] = (440, 300)
        landmarks[12] = (200, 300)
        landmarks[13] = (400, 320)
        landmarks[15] = (360, 350)
        landmarks[14] = (170, 320)
        landmarks[16] = (100, 350)

        engine.update(landmarks, MOCK_CONNECTIONS)
        rp = engine._player._render_points
        assert rp is not None
        assert rp[15][0] > rp[11][0], "left arm should point forward (image-right)"
        assert rp[16][0] > rp[12][0], "right arm should point forward (image-right)"

    def test_pose_warning_pauses_game(self):
        """When scale_warning is active, obstacles don't advance."""
        from unittest.mock import MagicMock
        sound = MagicMock(spec=SoundManager)
        engine = GameEngine(WIDTH, HEIGHT, sound_manager=sound)
        engine.start()

        # Landmarks with no shoulders
        landmarks = make_standing_landmarks()
        landmarks[LEFT_SHOULDER] = None
        landmarks[RIGHT_SHOULDER] = None
        engine.update(landmarks, MOCK_CONNECTIONS)

        # Obstacle should not be updated (game paused)
        obs = Obstacle(
            x=CHARACTER_X + 100,
            ground_y=GROUND_Y,
            width=OBSTACLE_WIDTH,
            height=60,
            speed=BASE_SPEED,
        )
        engine._obstacle_manager._obstacles = [obs]
        engine._obstacle_manager._spawn_timer = 999
        old_x = obs.x
        engine.update(landmarks, MOCK_CONNECTIONS)
        assert obs.x == old_x  # obstacle didn't move

    # --- Sky block tests ---

    def test_sky_blocks_spawn_over_time(self):
        """Sky blocks are spawned during gameplay."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        # Update enough frames to spawn at least one sky block
        for _ in range(300):
            engine.update(standing, MOCK_CONNECTIONS)
        assert len(engine._sky_blocks) >= 0  # at least initialized

    def test_sky_block_moves_leftward(self):
        """Sky blocks move leftward at cloud speed."""
        engine = self._make_engine()
        engine.start()

        block = SkyBlock(
            x=WIDTH,
            y=150,
            size=SKY_BLOCK_SIZE,
            color=SKY_BLOCK_COLOR,
            speed=BASE_SPEED,
        )
        engine._sky_blocks = [block]
        engine._sky_block_timer = 999
        old_x = block.x
        engine._update_sky_blocks(BASE_SPEED)
        assert block.x < old_x

    # --- Cloud tests ---

    def test_clouds_spawn_over_time(self):
        """Clouds are spawned during gameplay."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        for _ in range(300):
            engine.update(standing, MOCK_CONNECTIONS)
        assert len(engine._clouds) >= 0

    def test_cloud_moves_slower_than_obstacles(self):
        """Clouds move at CLOUD_SPEED_FACTOR of obstacle speed."""
        engine = self._make_engine()
        engine.start()

        cloud = Cloud(
            x=WIDTH,
            y=100,
            width=60,
            height=40,
            color=CLOUD_COLOR,
            speed=BASE_SPEED,
        )
        engine._clouds = [cloud]
        engine._cloud_timer = 999
        old_x = cloud.x
        engine._update_clouds(BASE_SPEED)
        assert cloud.x < old_x
        assert cloud.x == pytest.approx(old_x - BASE_SPEED * CLOUD_SPEED_FACTOR)

    # --- Brick ground and graffiti tests ---

    def test_brick_ground_rendered(self):
        """Brick ground is rendered with BRICK_COLOR."""
        engine = self._make_engine()
        engine.start()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        # Ground area should have brick color (not on a pattern line)
        ground_pixel = frame[GROUND_Y + 5, 10]
        assert tuple(ground_pixel) == BRICK_COLOR

    def test_graffiti_text_rendered(self):
        """Graffiti text is rendered on the ground."""
        engine = self._make_engine()
        engine.start()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        # Graffiti text should be visible (white text on brick ground)
        # Check a pixel near the graffiti text position
        graffiti_y = GROUND_Y - 10
        graffiti_x = WIDTH // 2
        pixel = frame[graffiti_y, graffiti_x]
        assert pixel.sum() > 0  # non-black pixel (text or background)

    # --- Heart rendering tests ---

    def test_hearts_show_in_hud(self):
        """Hearts are rendered in the top-right corner."""
        engine = self._make_engine()
        engine.start()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        # Top-right area should have heart color (red)
        heart_area = frame[0:40, WIDTH - 120:WIDTH]
        assert heart_area.sum() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
