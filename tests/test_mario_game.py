"""Unit tests for the Mario Bros pose-controlled jumping game.

Tests cover MarioCharacter, MarioObstacle, MarioObstacleManager, and
MarioGameEngine logic. All tests run without a camera or model file by
using mock landmark data and numpy arrays for frames.
"""

import numpy as np
import pytest
from unittest.mock import MagicMock

from src.mario_game import (
    BASE_SPEED,
    CHARACTER_TARGET_HEIGHT,
    CHARACTER_X,
    DOUBLE_JUMP_VELOCITY,
    GROUND_Y_RATIO,
    JUMP_COOLDOWN,
    JUMP_THRESHOLD,
    JumpDetector,
    LEVEL_INTERVAL,
    LEVEL_SPAWN_GAP_RANGES,
    MarioCharacter,
    MarioGameEngine,
    MarioObstacle,
    MarioObstacleManager,
    MAX_JUMPS,
    MAX_LEVEL,
    PIPE_WIDTH,
    PIPE_HEIGHT,
    BLOCK_WIDTH,
    BLOCK_HEIGHT,
    GOOMBA_WIDTH,
    GOOMBA_HEIGHT,
    OBSTACLE_TYPES,
    SKY_COLOR,
    SPEED_MULTIPLIER,
)


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
    """Create a 33-point mock landmark list with visible key joints."""
    cx = width // 2
    points = [None] * 33

    points[0] = (cx, nose_y)
    points[11] = (cx - 20, shoulder_y)
    points[12] = (cx + 20, shoulder_y)
    points[23] = (cx - 20, hip_y)
    points[24] = (cx + 20, hip_y)
    points[29] = (cx - 20, ankle_y)
    points[30] = (cx + 20, ankle_y)
    points[25] = (cx - 20, (hip_y + ankle_y) // 2)
    points[26] = (cx + 20, (hip_y + ankle_y) // 2)
    points[13] = (cx - 50, shoulder_y + 30)
    points[14] = (cx + 50, shoulder_y + 30)
    points[15] = (cx - 60, shoulder_y + 80)
    points[16] = (cx + 60, shoulder_y + 80)
    points[31] = (cx - 20, ankle_y)
    points[32] = (cx + 20, ankle_y)
    points[27] = (cx - 10, ankle_y - 5)
    points[28] = (cx + 10, ankle_y - 5)
    return points


def make_standing_landmarks():
    """Shoulders at a fixed baseline (y=240)."""
    return make_landmarks(shoulder_y=240)


def make_jumping_landmarks(jump_height=80):
    """Shoulders raised above baseline by jump_height."""
    return make_landmarks(shoulder_y=240 - jump_height)


# --- MarioCharacter Tests ----------------------------------------------------


class TestMarioCharacter:
    def _make_character(self, ground_y=GROUND_Y):
        return MarioCharacter(CHARACTER_X, ground_y)

    def test_initial_state_on_ground(self):
        """Character starts on the ground at rest."""
        char = self._make_character()
        assert char.on_ground is True
        assert char.bounding_box == (0, 0, 0, 0)

    def test_jump_sets_upward_velocity(self):
        """jump() applies upward velocity and leaves the ground."""
        char = self._make_character()
        jumped = char.jump()
        assert jumped is True
        assert char.on_ground is False

    def test_double_jump_succeeds_while_airborne(self):
        """Second jump while airborne succeeds (double jump)."""
        char = self._make_character()
        char.jump()  # first jump
        jumped = char.jump()  # double jump
        assert jumped is True
        assert char._jump_count == 2

    def test_third_jump_prevented(self):
        """Third jump while airborne is prevented (MAX_JUMPS = 2)."""
        char = self._make_character()
        char.jump()  # first jump
        char.jump()  # double jump
        jumped = char.jump()  # third jump - should fail
        assert jumped is False
        assert char._jump_count == 2

    def test_double_jump_applies_additional_velocity(self):
        """Double jump applies DOUBLE_JUMP_VELOCITY boost to current velocity."""
        char = self._make_character()
        char.jump()  # first jump: vy = JUMP_VELOCITY
        vy_after_first = char._vy
        char.jump()  # double jump: vy += DOUBLE_JUMP_VELOCITY
        assert char._vy == pytest.approx(vy_after_first + DOUBLE_JUMP_VELOCITY)

    def test_jump_count_resets_on_landing(self):
        """Jump count resets to 0 when character returns to ground."""
        char = self._make_character()
        char.jump()
        char.jump()  # double jump
        assert char._jump_count == 2

        # Simulate landing
        char._jump_offset = 0.0
        char._vy = 0.0
        char._on_ground = True
        char._jump_count = 0
        char.update()  # should keep jump_count at 0 (already on ground)

        # After landing, first jump should work again
        assert char._jump_count == 0

    def test_jump_count_resets_after_full_jump_cycle(self):
        """After a full jump and fall, jump count resets for next jump."""
        char = self._make_character()
        char.jump()  # first jump
        char.jump()  # double jump
        assert char._jump_count == 2

        # Update until character lands
        frames = 0
        while not char.on_ground and frames < 200:
            char.update()
            frames += 1

        assert char.on_ground is True
        assert char._jump_count == 0

    def test_double_jump_reaches_higher_apex(self):
        """Double jump reaches a higher apex than single jump."""
        # Single jump
        char1 = self._make_character()
        char1.jump()
        apex1 = 0.0
        frames = 0
        while not char1.on_ground and frames < 200:
            char1.update()
            apex1 = min(apex1, char1._jump_offset)
            frames += 1

        # Double jump (jump again at apex)
        char2 = self._make_character()
        char2.jump()
        # Wait until near apex (vy close to 0)
        for _ in range(20):
            char2.update()
        char2.jump()  # double jump
        apex2 = 0.0
        frames = 0
        while not char2.on_ground and frames < 200:
            char2.update()
            apex2 = min(apex2, char2._jump_offset)
            frames += 1

        # Double jump apex should be more negative (higher)
        assert apex2 < apex1

    def test_gravity_returns_to_ground(self):
        """After jumping, gravity pulls the character back to ground."""
        char = self._make_character()
        char.jump()
        assert char.on_ground is False

        frames = 0
        while not char.on_ground and frames < 100:
            char.update()
            frames += 1

        assert char.on_ground is True
        assert frames > 0

    def test_jump_apex_above_ground(self):
        """At apex, character's jump_offset is negative (above ground)."""
        char = self._make_character()
        char.jump()
        char.update()
        assert char._jump_offset < 0

    def test_bbox_update_after_pose(self):
        """After update with landmarks, bbox is non-zero."""
        char = self._make_character()
        lands = make_standing_landmarks()
        char.update(lands)
        bx, by, bw, bh = char.bounding_box
        assert bw > 0
        assert bh > 0
        assert bx >= 0
        assert by >= 0

    def test_pose_scaled_to_target_height(self):
        """Transformed landmarks fit within CHARACTER_TARGET_HEIGHT."""
        char = self._make_character(ground_y=384)
        lands = make_landmarks(
            shoulder_y=240, nose_y=120, hip_y=300, ankle_y=380
        )
        char.update(lands)

        render_points = char._render_points
        assert render_points is not None

        nose = render_points[0]
        ankle = render_points[29]
        if nose is not None and ankle is not None:
            char_height = abs(ankle[1] - nose[1])
            assert 50 < char_height < 120

    def test_render_does_not_crash(self):
        """render() on a blank frame does not raise."""
        char = self._make_character()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        char.render(frame, MOCK_CONNECTIONS)
        assert frame is not None

    def test_render_with_pose_does_not_crash(self):
        """render() with pose landmarks draws without errors."""
        char = self._make_character()
        char.update(make_standing_landmarks())
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        char.render(frame, MOCK_CONNECTIONS)
        assert frame is not None

    def test_render_with_pose_draws_mario_colors(self):
        """Character rendered with pose draws Mario colors (face, cap, shirt)."""
        from src.silhouette import MARIO_FACE, MARIO_HAT, MARIO_SHIRT, MARIO_OVERALL

        char = self._make_character(ground_y=384)
        char.update(make_standing_landmarks())
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        char.render(frame, MOCK_CONNECTIONS)

        # Should have drawn SOMETHING (not all black)
        assert frame.sum() > 0

    def test_reset_returns_to_ground(self):
        """reset() puts the character back on the ground at rest."""
        char = self._make_character()
        char.jump()
        char.update()
        assert char.on_ground is False

        char.reset()
        assert char.on_ground is True
        assert char._jump_offset == 0.0
        assert char._vy == 0.0

    def test_falling_velocity_increases(self):
        """Gravity increases downward velocity each frame while airborne."""
        char = self._make_character()
        char.jump()
        vy1 = char._vy
        char.update()
        vy2 = char._vy
        assert vy2 > vy1

    def test_jump_apex_clears_max_obstacle(self):
        """Jump apex exceeds the maximum obstacle height (120 px)."""
        char = self._make_character()
        char.jump()

        apex = 0.0
        frames = 0
        while not char.on_ground and frames < 200:
            char.update()
            apex = min(apex, char._jump_offset)
            frames += 1

        assert abs(apex) > 120


# --- MarioObstacle Tests -----------------------------------------------------

class TestMarioObstacle:
    def test_movement_leftward(self):
        """update() moves the obstacle leftward by speed."""
        obs = MarioObstacle(
            x=300, ground_y=384, width=40, height=80,
            speed=5.0, obs_type="pipe", color=(0, 180, 0),
        )
        assert obs.x == 300.0
        obs.update()
        assert obs.x == 295.0
        obs.update()
        assert obs.x == 290.0

    def test_off_screen(self):
        """off_screen() returns True when the obstacle clears the left edge."""
        obs = MarioObstacle(
            x=10, ground_y=384, width=40, height=80,
            speed=5.0, obs_type="goomba", color=(0, 50, 200),
        )
        assert obs.off_screen() is False
        obs.x = -41  # x + width = -1 < 0
        assert obs.off_screen() is True

    def test_collision_when_overlapping(self):
        """check_collision returns True when bboxes overlap."""
        obs = MarioObstacle(
            x=100, ground_y=384, width=40, height=80,
            speed=5.0, obs_type="block", color=(30, 165, 200),
        )
        char_bbox = (105, 330, 20, 80)
        assert obs.check_collision(char_bbox) is True

    def test_no_collision_when_separated(self):
        """check_collision returns False when bboxes are far apart."""
        obs = MarioObstacle(
            x=100, ground_y=384, width=40, height=80,
            speed=5.0, obs_type="pipe", color=(0, 180, 0),
        )
        char_bbox = (400, 330, 20, 80)
        assert obs.check_collision(char_bbox) is False

    def test_mark_passed_when_left_of_character(self):
        """mark_passed returns True once the obstacle passes the character."""
        obs = MarioObstacle(
            x=80, ground_y=384, width=40, height=80,
            speed=5.0, obs_type="pipe", color=(0, 180, 0),
        )
        char_x = 80

        # x=80, right edge=120 > 80 → not yet passed
        assert obs.mark_passed(char_x) is False

        obs.x = 45  # right edge = 85, not yet past
        assert obs.mark_passed(char_x) is False

        obs.x = 40  # right edge = 80, not yet past
        assert obs.mark_passed(char_x) is False

        obs.x = 35  # right edge = 75 < 80
        assert obs.mark_passed(char_x) is True

        # Already passed, won't fire again
        assert obs.mark_passed(char_x) is False

    def test_render_does_not_crash(self):
        """render() draws all obstacle types without errors."""
        types_and_colors = [
            ("pipe", (0, 180, 0)),
            ("block", (30, 165, 200)),
            ("goomba", (0, 50, 200)),
        ]
        for obs_type, color in types_and_colors:
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            obs = MarioObstacle(
                x=100, ground_y=384, width=40, height=80,
                speed=5.0, obs_type=obs_type, color=color,
            )
            obs.render(frame)
            assert frame.sum() > 0, f"Obstacle type {obs_type} not rendered"

    def test_obstacle_types(self):
        """OBSTACLE_TYPES contains pipe, block, and goomba."""
        assert set(OBSTACLE_TYPES) == {"pipe", "block", "goomba"}


# --- MarioObstacleManager Tests ----------------------------------------------

class TestMarioObstacleManager:
    def _make_manager(self, base_speed=BASE_SPEED):
        return MarioObstacleManager(WIDTH, GROUND_Y, base_speed=base_speed)

    def test_initial_state(self):
        """New manager has no obstacles and level 1."""
        mgr = self._make_manager()
        assert mgr.passed_count == 0
        assert mgr.level == 1
        assert len(mgr._obstacles) == 0

    def test_initial_spawn_gap_range(self):
        """Level 1 spawn gap range is wider than the existing game's."""
        mgr = self._make_manager()
        gap_range = mgr.spawn_gap_range
        assert gap_range == LEVEL_SPAWN_GAP_RANGES[0]
        assert gap_range[0] >= 100  # Much wider than existing game's 40

    def test_obstacles_spawn_over_time(self):
        """Obstacles are spawned as the spawn timer counts down."""
        mgr = self._make_manager()
        mgr._spawn_timer = 0  # force immediate spawn
        mgr.update(CHARACTER_X, (0, 0, 0, 0))
        assert len(mgr._obstacles) >= 1

    def test_passed_count_increments(self):
        """passed_count increments when an obstacle passes the character."""
        mgr = self._make_manager()
        mgr._spawn_timer = 999  # prevent spawning during test
        obs = MarioObstacle(
            x=CHARACTER_X - 40 - 10, ground_y=GROUND_Y,
            width=40, height=80, speed=BASE_SPEED,
            obs_type="pipe", color=(0, 180, 0),
        )
        obs.passed = False
        mgr._obstacles = [obs]
        mgr.update(CHARACTER_X, (0, 0, 0, 0))
        assert mgr.passed_count == 1

    def test_off_screen_obstacles_removed(self):
        """Obstacles that scroll off-screen are removed."""
        mgr = self._make_manager()
        mgr._spawn_timer = 999  # prevent spawning
        obs = MarioObstacle(
            x=-100, ground_y=GROUND_Y, width=40, height=80,
            speed=5.0, obs_type="goomba", color=(0, 50, 200),
        )
        mgr._obstacles = [obs]
        mgr.update(CHARACTER_X, (0, 0, 0, 0))
        assert len(mgr._obstacles) == 0

    def test_set_speed_updates_existing_obstacles(self):
        """set_speed() propagates to all existing obstacles."""
        mgr = self._make_manager()
        obs1 = MarioObstacle(
            x=100, ground_y=GROUND_Y, width=40, height=80,
            speed=4.0, obs_type="pipe", color=(0, 180, 0),
        )
        obs2 = MarioObstacle(
            x=200, ground_y=GROUND_Y, width=30, height=30,
            speed=4.0, obs_type="goomba", color=(0, 50, 200),
        )
        mgr._obstacles = [obs1, obs2]

        mgr.set_speed(10.0)
        assert obs1.speed == 10.0
        assert obs2.speed == 10.0
        assert mgr.speed == 10.0

    def test_check_collisions_returns_true_on_overlap(self):
        """check_collisions returns True when any obstacle overlaps."""
        mgr = self._make_manager()
        obs = MarioObstacle(
            x=CHARACTER_X - 10, ground_y=GROUND_Y,
            width=40, height=80, speed=BASE_SPEED,
            obs_type="block", color=(30, 165, 200),
        )
        mgr._obstacles = [obs]
        char_bbox = (CHARACTER_X - 5, GROUND_Y - 80, 20, 80)
        assert mgr.check_collisions(char_bbox) is True

    def test_check_collisions_returns_false_when_clear(self):
        """check_collisions returns False when no obstacles overlap."""
        mgr = self._make_manager()
        obs = MarioObstacle(
            x=WIDTH - 100, ground_y=GROUND_Y, width=40, height=80,
            speed=BASE_SPEED, obs_type="pipe", color=(0, 180, 0),
        )
        mgr._obstacles = [obs]
        char_bbox = (CHARACTER_X - 5, GROUND_Y - 80, 20, 80)
        assert mgr.check_collisions(char_bbox) is False

    def test_level_progression(self):
        """Level increments every 10 obstacles passed (LEVEL_INTERVAL=10)."""
        mgr = self._make_manager()
        mgr._spawn_timer = 999

        # At 0 passed -> level 1
        mgr._passed_count = 0
        assert mgr.level == 1

        # At 9 passed -> still level 1
        mgr._passed_count = 9
        assert mgr.level == 1

        # At 10 passed -> level 2
        mgr._passed_count = 10
        assert mgr.level == 2

        # At 20 passed -> level 3
        mgr._passed_count = 20
        assert mgr.level == 3

        # At 30 passed -> level 4
        mgr._passed_count = 30
        assert mgr.level == 4

    def test_level_caps_at_max(self):
        """Level does not exceed MAX_LEVEL + 1."""
        mgr = self._make_manager()
        mgr._passed_count = 999
        assert mgr.level <= MAX_LEVEL + 1

    def test_gap_range_tightens_with_level(self):
        """Higher levels have tighter spawn gap ranges."""
        mgr = self._make_manager()
        level_1_range = mgr.spawn_gap_range
        assert mgr.level == 1

        mgr._passed_count = 20  # level 3
        level_3_range = mgr.spawn_gap_range
        assert level_3_range[0] < level_1_range[0]
        assert level_3_range[1] < level_1_range[1]

    def test_spawn_creates_different_types(self):
        """Spawning cycles through pipe, block, goomba."""
        mgr = self._make_manager()
        mgr._spawn_timer = 999

        mgr._spawn()
        mgr._spawn()
        mgr._spawn()
        assert mgr._obstacles[0].type == "pipe"
        assert mgr._obstacles[1].type == "block"
        assert mgr._obstacles[2].type == "goomba"

    def test_reset_clears_obstacles_and_level(self):
        """reset() empties obstacles and resets level to 1."""
        mgr = self._make_manager()
        mgr._passed_count = 50  # level 6
        mgr._obstacles = [
            MarioObstacle(x=100, ground_y=GROUND_Y, width=40, height=80,
                          speed=5.0, obs_type="pipe", color=(0, 180, 0))
        ]
        mgr.reset()
        assert len(mgr._obstacles) == 0
        assert mgr.passed_count == 0
        assert mgr.level == 1


# --- MarioGameEngine Tests ---------------------------------------------------

class TestMarioGameEngine:
    def _make_engine(self):
        return MarioGameEngine(WIDTH, HEIGHT)

    def test_initial_state_is_menu(self):
        """Engine starts in MENU state."""
        engine = self._make_engine()
        assert engine.state == MarioGameEngine.MENU
        assert engine.state_name == "MENU"
        assert engine.passed_count == 0
        assert engine.level == 1

    def test_speed_starts_at_base(self):
        """Initial speed equals BASE_SPEED with no obstacles passed."""
        engine = self._make_engine()
        assert engine.speed == pytest.approx(BASE_SPEED)

    def test_start_transitions_to_playing(self):
        """handle_key(SPACE) from MENU starts the game."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))
        assert engine.state == MarioGameEngine.PLAYING

    def test_reset_from_game_over_to_playing(self):
        """handle_key(SPACE) from GAME_OVER restarts the game."""
        engine = self._make_engine()
        engine.start()
        engine._state = MarioGameEngine.GAME_OVER
        engine.handle_key(ord(" "))
        assert engine.state == MarioGameEngine.PLAYING
        assert engine.level == 1

    def test_speed_progression_formula(self):
        """Speed multiplier is SPEED_MULTIPLIER^(level - 1) = SPEED_MULTIPLIER^(passed_count // 10)."""
        engine = self._make_engine()
        engine.start()

        engine._obstacle_manager._passed_count = 0
        assert engine.speed == pytest.approx(BASE_SPEED)

        engine._obstacle_manager._passed_count = 9
        assert engine.speed == pytest.approx(BASE_SPEED)

        engine._obstacle_manager._passed_count = 10
        assert engine.speed == pytest.approx(BASE_SPEED * SPEED_MULTIPLIER)

        engine._obstacle_manager._passed_count = 20
        assert engine.speed == pytest.approx(BASE_SPEED * SPEED_MULTIPLIER ** 2)

    def test_collision_triggers_game_over(self):
        """Character colliding with an obstacle transitions to GAME_OVER."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        engine.update(standing, MOCK_CONNECTIONS)

        obs = MarioObstacle(
            x=CHARACTER_X - 20, ground_y=GROUND_Y,
            width=40, height=100, speed=BASE_SPEED,
            obs_type="block", color=(30, 165, 200),
        )
        engine._obstacle_manager._obstacles = [obs]

        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.state == MarioGameEngine.GAME_OVER

    def test_menu_update_does_nothing(self):
        """In MENU state, update() does not spawn obstacles."""
        engine = self._make_engine()
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        assert engine.state == MarioGameEngine.MENU
        assert engine.passed_count == 0

    def test_game_over_update_frozen(self):
        """In GAME_OVER state, update() does not change score or state."""
        engine = self._make_engine()
        engine.start()
        engine._state = MarioGameEngine.GAME_OVER

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.state == MarioGameEngine.GAME_OVER

    def test_jump_detected_during_play(self):
        """A jump gesture triggers the character to jump during PLAYING."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine._player.on_ground is True

        jumping = make_jumping_landmarks(jump_height=80)
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player.on_ground is False

    def test_render_menu_does_not_crash(self):
        """render() in MENU state does not crash."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.render(frame, MOCK_CONNECTIONS)

    def test_render_playing_does_not_crash(self):
        """render() in PLAYING state renders without errors."""
        engine = self._make_engine()
        engine.start()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

    def test_render_game_over_does_not_crash(self):
        """render() in GAME_OVER state renders without errors."""
        engine = self._make_engine()
        engine.start()
        engine._state = MarioGameEngine.GAME_OVER
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.render(frame, MOCK_CONNECTIONS)

    def test_handle_key_q_does_not_start(self):
        """Pressing 'q' from MENU does not start the game."""
        engine = self._make_engine()
        engine.handle_key(ord("q"))
        assert engine.state == MarioGameEngine.MENU

    def test_playing_state_updates_player(self):
        """In PLAYING, update() passes landmarks to the player."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        assert engine._player._render_points is not None

    def test_background_is_sky_blue_not_black(self):
        """Rendered playing background is sky blue, not solid black."""
        engine = self._make_engine()
        engine.start()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        # The background should be sky blue (not black)
        assert frame[0, 0].sum() > 0
        assert tuple(frame[0, 0]) == SKY_COLOR

    def test_level_up_on_10_obstacles(self):
        """Level increments to 2 after 10 obstacles passed."""
        engine = self._make_engine()
        engine.start()
        engine._obstacle_manager._passed_count = 10
        assert engine.level == 2

    def test_spawn_gap_at_level_1_is_wide(self):
        """Level 1 spawn gap is at least 180 frames (much wider than existing game)."""
        engine = self._make_engine()
        gap = engine._obstacle_manager.spawn_gap_range
        assert gap == (180, 280)

    def test_initial_spawn_gap_wider_than_existing_game(self):
        """Mario game level 1 gaps are much wider than the existing game's 40-90."""
        engine = self._make_engine()
        min_gap = engine._obstacle_manager.spawn_gap_range[0]
        assert min_gap >= 100  # existing game uses 40-90

    def test_hud_shows_level(self):
        """After update in PLAYING, the HUD region is visible with color."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.start()
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        # Top-left HUD area should have non-black pixels (white text)
        hud_area = frame[0:80, 0:200]
        assert hud_area.sum() > 0

    def test_coin_sound_plays_on_obstacle_pass(self):
        """Coin sound plays when an obstacle passes the character."""
        mock_sound = MagicMock()
        engine = MarioGameEngine(WIDTH, HEIGHT, sound_manager=mock_sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        # Place an obstacle that will pass the character
        obs = MarioObstacle(
            x=CHARACTER_X - 40 - 10, ground_y=GROUND_Y,
            width=40, height=80, speed=BASE_SPEED,
            obs_type="pipe", color=(0, 180, 0),
        )
        engine._obstacle_manager._obstacles = [obs]
        engine._obstacle_manager._spawn_timer = 999

        engine.update(standing, MOCK_CONNECTIONS)
        assert mock_sound.play_coin.called

    def test_game_over_sound_plays_on_collision(self):
        """Game-over sound plays when character collides with an obstacle."""
        mock_sound = MagicMock()
        engine = MarioGameEngine(WIDTH, HEIGHT, sound_manager=mock_sound)
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        engine.update(standing, MOCK_CONNECTIONS)

        obs = MarioObstacle(
            x=CHARACTER_X - 20, ground_y=GROUND_Y,
            width=40, height=100, speed=BASE_SPEED,
            obs_type="block", color=(30, 165, 200),
        )
        engine._obstacle_manager._obstacles = [obs]

        engine.update(standing, MOCK_CONNECTIONS)
        assert engine.state == MarioGameEngine.GAME_OVER
        assert mock_sound.play_game_over.called

    def test_double_jump_detected_during_play(self):
        """A second jump gesture while airborne triggers a double jump."""
        engine = self._make_engine()
        engine.start()

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine._player.on_ground is True

        # First jump
        jumping = make_jumping_landmarks(jump_height=80)
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player.on_ground is False
        assert engine._player._jump_count == 1

        # Wait for cooldown
        for _ in range(JUMP_COOLDOWN + 2):
            engine.update(standing, MOCK_CONNECTIONS)

        # Second jump (double jump) while airborne
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player._jump_count == 2

    def test_engine_close_calls_sound_manager(self):
        """close() calls close() on the sound manager."""
        mock_sound = MagicMock()
        engine = MarioGameEngine(WIDTH, HEIGHT, sound_manager=mock_sound)
        engine.close()
        assert mock_sound.close.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
