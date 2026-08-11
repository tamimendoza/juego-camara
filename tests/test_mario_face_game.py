"""Unit tests for the Mario Face game variant.

Tests cover MarioFaceCharacter, FaceCropper, FaceDetector, and
MarioFaceGameEngine logic. All tests run without a camera or model file by
using mock landmark data and numpy arrays for frames.
"""

import cv2
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.mario_face_game import (
    MarioFaceCharacter,
    MarioFaceGameEngine,
    RESOLUTION,
    WINDOW_NAME,
    SPEED_INCREMENT,
    GRAFFITI_BRICK_Y_OFFSET,
)
from src.mario_game import (
    BASE_SPEED,
    CHARACTER_TARGET_HEIGHT,
    CHARACTER_X,
    GRAVITY,
    GROUND_Y_RATIO,
    INVINCIBILITY_THRESHOLD,
    JUMP_COOLDOWN,
    JUMP_THRESHOLD,
    LEFT_SHOULDER,
    MAX_JUMPS,
    MAX_LIVES,
    OBSTACLE_TYPES,
    PIPE_WIDTH,
    PIPE_HEIGHT,
    BLOCK_WIDTH,
    BLOCK_HEIGHT,
    GOOMBA_WIDTH,
    GOOMBA_HEIGHT,
    POSE_WARNING_COLOR,
    POSE_WARNING_TEXT,
    RIGHT_SHOULDER,
    SKY_COLOR,
    SKY_BLOCK_SIZE,
    SKY_BLOCK_COLOR,
    SKY_BLOCK_SPAWN_INTERVAL,
    SKY_BLOCK_HEIGHT_RANGE,
    SkyBlock,
    Cloud,
    CLOUD_COLOR,
    CLOUD_SPEED_FACTOR,
    CLOUD_SPAWN_INTERVAL,
    CLOUD_SIZE_RANGE,
    MarioCharacter,
    MarioGameEngine,
    MarioObstacle,
    MarioObstacleManager,
    SPEED_MULTIPLIER,
    HUD_COLOR,
    DOUBLE_JUMP_VELOCITY,
    LEVEL_INTERVAL,
    LEVEL_SPAWN_GAP_RANGES,
)
from src.face_crop import FaceCropper
from src.face_detector import FaceDetector
from src.face_landmarker import FaceLandmarkerDetector
from src.silhouette import SilhouetteDrawer, MARIO_FACE, MARIO_SHIRT, MARIO_OVERALL


# --- Helpers -----------------------------------------------------------------

WIDTH, HEIGHT = 640, 480
GROUND_Y = int(HEIGHT * GROUND_Y_RATIO)

MOCK_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (11, 12),
    (11, 13), (13, 15), (15, 16), (16, 18),
    (12, 14), (14, 16),
    (11, 23), (12, 24),
    (23, 24),
    (23, 25), (25, 27), (27, 29),
    (24, 26), (26, 28), (28, 30),
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
    return make_landmarks(shoulder_y=240)


def make_jumping_landmarks(jump_height=80):
    return make_landmarks(shoulder_y=240 - jump_height)


def make_face_landmarks(nose_x=320, nose_y=240, width=WIDTH, height=HEIGHT):
    """Create mock FaceMesh landmarks (468 points) with the nose tip at a known position."""
    landmarks = []
    for i in range(468):
        # FaceMesh landmarks are normalized [0, 1]
        if i == 1:  # nose tip
            x = nose_x / width
            y = nose_y / height
        else:
            # Spread points around the nose in a circle
            angle = (i / 468) * 2 * np.pi
            offset = 40 / width
            x = nose_x / width + np.cos(angle) * offset
            y = nose_y / height + np.sin(angle) * offset
        class Lm:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        landmarks.append(Lm(x, y, 0.0))
    return landmarks


def make_face_landmark_list(nose_x=320, nose_y=240, width=WIDTH, height=HEIGHT):
    """Wrap landmarks in a NormalizedLandmarkList-like object (has .landmark attr)."""
    class LandmarkList:
        def __init__(self, landmark):
            self.landmark = landmark
    return LandmarkList(make_face_landmarks(nose_x, nose_y, width, height))


def make_mock_face_detector(detect_result=None):
    """Create a mock FaceDetector that returns the given result from detect()."""
    mock = MagicMock(spec=FaceDetector)
    mock.detect.return_value = detect_result
    mock.close.return_value = None
    return mock


def make_mock_face_cropper(crop_result=None):
    """Create a mock FaceCropper that returns the given result from crop_face()."""
    mock = MagicMock(spec=FaceCropper)
    mock.crop_face.return_value = crop_result
    return mock


def make_mock_face_landmarker(detect_result=None):
    """Create a mock FaceLandmarkerDetector that returns the given result from detect().

    The real detector returns (face_landmarks, face_bbox).  Pass a tuple for
    detect_result; defaults to (None, None).
    """
    mock = MagicMock(spec=FaceLandmarkerDetector)
    mock.detect.return_value = detect_result if detect_result is not None else (None, None)
    mock.close.return_value = None
    return mock


def make_face_crop(radius=20):
    """Create a simple face crop (BGR image + circular mask)."""
    size = radius * 2
    face_img = np.full((size, size, 3), (100, 150, 200), dtype=np.uint8)
    mask = np.zeros((size, size), dtype=np.uint8)
    cv2.circle(mask, (radius, radius), radius, 255, -1)
    return face_img, mask


# --- MarioFaceCharacter Tests ------------------------------------------------

class TestMarioFaceCharacter:
    def _make_character(self, ground_y=GROUND_Y):
        return MarioFaceCharacter(CHARACTER_X, ground_y)

    def test_inherits_jump_physics(self):
        """MarioFaceCharacter inherits jump physics from MarioCharacter."""
        char = self._make_character()
        jumped = char.jump()
        assert jumped is True
        assert char.on_ground is False

    def test_inherits_double_jump(self):
        """Double jump works identically to MarioCharacter."""
        char = self._make_character()
        char.jump()
        jumped = char.jump()
        assert jumped is True
        assert char._jump_count == 2

    def test_inherits_third_jump_prevented(self):
        """Third jump is prevented (MAX_JUMPS = 2)."""
        char = self._make_character()
        char.jump()
        char.jump()
        jumped = char.jump()
        assert jumped is False

    def test_inherits_reset(self):
        """reset() works identically to MarioCharacter."""
        char = self._make_character()
        char.jump()
        char.reset()
        assert char.on_ground is True
        assert char._jump_offset == 0.0
        assert char._render_points is None
        assert char.bounding_box == (0, 0, 0, 0)

    def test_inherits_bbox_after_pose(self):
        """bbox is computed after pose update, same as MarioCharacter."""
        char = self._make_character(ground_y=384)
        char.update(make_standing_landmarks())
        bx, by, bw, bh = char.bounding_box
        assert bw > 0
        assert bh > 0

    def test_render_with_face_image_does_not_crash(self):
        """render() with face_image passes face_overlay style to drawer."""
        char = self._make_character(ground_y=384)
        char.update(make_standing_landmarks())
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        face_img, face_mask = make_face_crop()
        char.render(frame, MOCK_CONNECTIONS, face_image=face_img, face_mask=face_mask)

        assert frame is not None
        assert frame.sum() > 0

    def test_render_without_face_image_draws_mario_head(self):
        """render() without face_image falls back to mario_head + mario_body styles."""
        from src.silhouette import MARIO_FACE, MARIO_HAT

        char = self._make_character(ground_y=384)
        char.update(make_standing_landmarks())
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        char.render(frame, MOCK_CONNECTIONS, face_image=None, face_mask=None)

        # Should draw peach face circle somewhere at the nose position
        assert frame.sum() > 0

    def test_render_without_face_draws_mario_colors(self):
        """Character rendered without face draws Mario colors (face, cap, shirt)."""
        char = self._make_character(ground_y=384)
        char.update(make_standing_landmarks())
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        char.render(frame, MOCK_CONNECTIONS, face_image=None, face_mask=None)

        # Should have red pixels (cap/shirt)
        red_pixels = np.all(frame == np.array(MARIO_SHIRT).reshape(1, 1, 3), axis=2)
        assert red_pixels.sum() > 0

    def test_render_no_pose_calls_fallback(self):
        """render() with no pose landmarks draws a static fallback figure."""
        char = self._make_character()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        char.render(frame, MOCK_CONNECTIONS, face_image=None, face_mask=None)

        # Fallback should draw something
        assert frame.sum() > 0


# --- FaceCropper Tests -------------------------------------------------------

class TestFaceCropper:
    def test_crop_face_returns_image_and_mask(self):
        """crop_face returns a BGR image and a single-channel mask."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmarks = make_face_landmarks(nose_x=320, nose_y=240)

        result = cropper.crop_face(bgr_frame, landmarks, 640, 480, 40)

        assert result is not None
        face_img, face_mask = result
        assert face_img.shape == (80, 80, 3)  # 40 * 2
        assert face_mask.shape == (80, 80)
        assert face_mask.dtype == np.uint8

    def test_crop_face_creates_circular_mask(self):
        """The face mask is circular: center opaque, corners transparent."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmarks = make_face_landmarks(nose_x=320, nose_y=240)

        face_img, face_mask = cropper.crop_face(bgr_frame, landmarks, 640, 480, 40)

        # Center should be opaque
        assert face_mask[40, 40] == 255
        # Corners should be transparent
        assert face_mask[0, 0] == 0
        assert face_mask[79, 79] == 0

    def test_crop_face_resizes_to_target(self):
        """crop_face resizes the face region to target_radius * 2."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmarks = make_face_landmarks(nose_x=320, nose_y=240)

        face_img, face_mask = cropper.crop_face(bgr_frame, landmarks, 640, 480, 20)

        assert face_img.shape == (40, 40, 3)
        assert face_mask.shape == (40, 40)

    def test_crop_face_returns_none_for_none_landmarks(self):
        """crop_face returns None when face_landmarks is None."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)

        result = cropper.crop_face(bgr_frame, None, 640, 480, 40)
        assert result is None

    def test_crop_face_returns_none_for_empty_landmarks(self):
        """crop_face returns None when face_landmarks is empty."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)

        result = cropper.crop_face(bgr_frame, [], 640, 480, 40)
        assert result is None

    def test_crop_face_accepts_normalized_landmark_list(self):
        """crop_face works when given a media.pipe NormalizedLandmarkList object."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmark_list = make_face_landmark_list(nose_x=320, nose_y=240)

        result = cropper.crop_face(bgr_frame, landmark_list, 640, 480, 40)

        assert result is not None
        face_img, face_mask = result
        assert face_img.shape == (80, 80, 3)
        assert face_mask.shape == (80, 80)

    def test_overlay_face_blends_face_onto_frame(self):
        """overlay_face blends the face image onto the frame at the center."""
        import cv2
        cropper = FaceCropper()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        mask = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(mask, (20, 20), 20, 255, -1)

        cropper.overlay_face(frame, face_img, mask, (320, 240), 20)

        # Center pixel should be the face color
        assert tuple(frame[240, 320]) == (100, 150, 200)

    def test_overlay_face_clamps_to_frame_bounds(self):
        """overlay_face handles face placement near frame edges."""
        import cv2
        cropper = FaceCropper()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        mask = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(mask, (20, 20), 20, 255, -1)

        # Place near top-left corner; should not crash or go out of bounds
        cropper.overlay_face(frame, face_img, mask, (10, 10), 20)

        assert frame.sum() > 0

    def test_overlay_face_with_none_does_not_crash(self):
        """overlay_face is a no-op when face_image or face_mask is None."""
        cropper = FaceCropper()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        cropper.overlay_face(frame, None, None, (320, 240), 20)
        assert frame.sum() == 0

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        cropper.overlay_face(frame, face_img, None, (320, 240), 20)
        assert frame.sum() == 0

    def test_crop_face_with_bbox_uses_bbox_center(self):
        """crop_face with face_bbox centers the crop on the bounding box."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmarks = make_face_landmarks(nose_x=320, nose_y=240)
        face_bbox = (280, 200, 80, 80)  # center at (320, 240)

        result = cropper.crop_face(
            bgr_frame, landmarks, 640, 480, 40, face_bbox=face_bbox
        )

        assert result is not None
        face_img, face_mask = result
        assert face_img.shape == (80, 80, 3)
        assert face_mask.shape == (80, 80)

    def test_crop_face_with_bbox_uses_contour_fallback_when_none(self):
        """crop_face with face_bbox=None falls back to contour landmarks."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmarks = make_face_landmarks(nose_x=320, nose_y=240)

        result_no_bbox = cropper.crop_face(bgr_frame, landmarks, 640, 480, 40)
        result_with_none = cropper.crop_face(
            bgr_frame, landmarks, 640, 480, 40, face_bbox=None
        )

        assert result_no_bbox is not None
        assert result_with_none is not None
        # Both should produce same-size output
        assert result_no_bbox[0].shape == result_with_none[0].shape

    def test_crop_face_with_bbox_produces_circular_mask(self):
        """crop_face with face_bbox still produces a circular mask."""
        cropper = FaceCropper()
        bgr_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmarks = make_face_landmarks(nose_x=320, nose_y=240)
        face_bbox = (280, 200, 80, 80)

        face_img, face_mask = cropper.crop_face(
            bgr_frame, landmarks, 640, 480, 40, face_bbox=face_bbox
        )

        assert face_mask[40, 40] == 255  # center opaque
        assert face_mask[0, 0] == 0      # corner transparent

class TestFaceDetector:
    def test_detect_returns_landmarks_when_face_found(self):
        """detect() returns face landmarks when FaceMesh detects a face."""
        with patch("mediapipe.solutions.face_mesh.FaceMesh") as MockFM:
            mock_instance = MagicMock()
            mock_landmarks = make_face_landmarks()

            mock_results = MagicMock()
            mock_results.multi_face_landmarks = [mock_landmarks]
            mock_instance.process.return_value = mock_results
            MockFM.return_value = mock_instance

            detector = FaceDetector()
            result = detector.detect(np.zeros((480, 640, 3), dtype=np.uint8))

            assert result is not None
            assert result == mock_landmarks

    def test_detect_returns_none_when_no_face(self):
        """detect() returns None when FaceMesh finds no face."""
        with patch("mediapipe.solutions.face_mesh.FaceMesh") as MockFM:
            mock_instance = MagicMock()
            mock_results = MagicMock()
            mock_results.multi_face_landmarks = None
            mock_instance.process.return_value = mock_results
            MockFM.return_value = mock_instance

            detector = FaceDetector()
            result = detector.detect(np.zeros((480, 640, 3), dtype=np.uint8))

            assert result is None

    def test_detect_returns_none_when_empty_list(self):
        """detect() returns None when FaceMesh returns an empty list."""
        with patch("mediapipe.solutions.face_mesh.FaceMesh") as MockFM:
            mock_instance = MagicMock()
            mock_results = MagicMock()
            mock_results.multi_face_landmarks = []
            mock_instance.process.return_value = mock_results
            MockFM.return_value = mock_instance

            detector = FaceDetector()
            result = detector.detect(np.zeros((480, 640, 3), dtype=np.uint8))

            assert result is None

    def test_close_does_not_raise(self):
        """close() releases FaceMesh resources without error."""
        with patch("mediapipe.solutions.face_mesh.FaceMesh") as MockFM:
            mock_instance = MagicMock()
            MockFM.return_value = mock_instance

            detector = FaceDetector()
            detector.close()  # should not raise

            assert mock_instance.close.called


# --- FaceLandmarkerDetector Tests ---------------------------------------------

class FakeFaceLandmarkerResult:
    """Mock of FaceLandmarkerResult for testing."""

    def __init__(self, face_landmarks=None):
        self.face_landmarks = face_landmarks if face_landmarks is not None else []


def make_face_landmarker_with_mock():
    """Create a FaceLandmarkerDetector that bypasses __init__ (no model file needed)."""
    detector = FaceLandmarkerDetector.__new__(FaceLandmarkerDetector)
    detector._landmarker = MagicMock()
    detector._last_timestamp = 0
    return detector


class TestFaceLandmarkerDetector:
    def test_detect_returns_landmarks_and_bbox_when_face_found(self):
        """detect() returns face landmarks and a computed bbox when a face is found."""
        detector = make_face_landmarker_with_mock()
        mock_landmarks = make_face_landmarks(nose_x=320, nose_y=240)
        detector._landmarker.detect_for_video.return_value = FakeFaceLandmarkerResult(
            face_landmarks=[mock_landmarks]
        )

        rgb_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        result_landmarks, result_bbox = detector.detect(rgb_frame)

        assert result_landmarks is not None
        assert len(result_landmarks) == 468
        assert result_bbox is not None
        assert len(result_bbox) == 4  # (x, y, width, height)

    def test_detect_bbox_computed_from_landmarks(self):
        """detect() computes the bbox from face landmark min/max coordinates."""
        detector = make_face_landmarker_with_mock()
        # Landmarks centered at (320, 240), spread ~40px around
        mock_landmarks = make_face_landmarks(nose_x=320, nose_y=240)
        detector._landmarker.detect_for_video.return_value = FakeFaceLandmarkerResult(
            face_landmarks=[mock_landmarks]
        )

        rgb_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        _, bbox = detector.detect(rgb_frame)

        x, y, w, h = bbox
        assert x > 0 and x < 640
        assert y > 0 and y < 480
        assert w > 0 and h > 0

    def test_detect_returns_none_when_no_face(self):
        """detect() returns (None, None) when FaceLandmarker detects no face."""
        detector = make_face_landmarker_with_mock()
        detector._landmarker.detect_for_video.return_value = FakeFaceLandmarkerResult(
            face_landmarks=[]
        )

        rgb_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        landmarks, bbox = detector.detect(rgb_frame)

        assert landmarks is None
        assert bbox is None

    def test_detect_auto_generates_timestamp(self):
        """detect() generates a monotonic timestamp when one is not provided."""
        detector = make_face_landmarker_with_mock()
        detector._landmarker.detect_for_video.return_value = FakeFaceLandmarkerResult(
            face_landmarks=[]
        )

        rgb_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        detector.detect(rgb_frame)

        call_args = detector._landmarker.detect_for_video.call_args
        assert call_args is not None
        assert len(call_args[0]) == 2  # image + timestamp_ms

    def test_detect_uses_explicit_timestamp(self):
        """detect() uses the provided timestamp."""
        detector = make_face_landmarker_with_mock()
        detector._landmarker.detect_for_video.return_value = FakeFaceLandmarkerResult(
            face_landmarks=[]
        )

        rgb_frame = np.full((480, 640, 3), (50, 100, 150), dtype=np.uint8)
        detector.detect(rgb_frame, timestamp_ms=99999)

        call_args = detector._landmarker.detect_for_video.call_args
        assert call_args[0][1] == 99999

    def test_init_raises_filenotfound_when_model_missing(self):
        """FaceLandmarkerDetector raises FileNotFoundError when model file is missing."""
        with pytest.raises(FileNotFoundError, match="Face landmark model file not found"):
            FaceLandmarkerDetector(model_path="/nonexistent/face_landmarker.task")

    def test_close_calls_landmarker_close(self):
        """close() releases the underlying FaceLandmarker resources."""
        detector = make_face_landmarker_with_mock()
        detector.close()
        assert detector._landmarker.close.called


# --- MarioFaceGameEngine Tests -----------------------------------------------

class TestMarioFaceGameEngine:
    def _make_engine(self, mock_face_landmarker=None, mock_face_cropper=None):
        """Create a MarioFaceGameEngine with mock face components."""
        if mock_face_landmarker is None:
            mock_face_landmarker = MagicMock(spec=FaceLandmarkerDetector)
            mock_face_landmarker.detect.return_value = (None, None)
            mock_face_landmarker.close.return_value = None
        if mock_face_cropper is None:
            mock_face_cropper = MagicMock(spec=FaceCropper)
            mock_face_cropper.crop_face.return_value = None

        engine = MarioFaceGameEngine(
            WIDTH, HEIGHT,
            sound_manager=MagicMock(),
            face_landmarker=mock_face_landmarker,
            face_cropper=mock_face_cropper,
        )
        return engine

    def test_initial_state_is_menu(self):
        """Engine starts in MENU state."""
        engine = self._make_engine()
        assert engine.state == MarioGameEngine.MENU
        assert engine.passed_count == 0
        assert engine.level == 1

    def test_player_is_mario_face_character(self):
        """The engine's player is a MarioFaceCharacter instance."""
        engine = self._make_engine()
        assert isinstance(engine._player, MarioFaceCharacter)

    def test_start_transitions_to_playing(self):
        """handle_key(SPACE) from MENU starts the game."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))
        assert engine.state == MarioGameEngine.PLAYING

    def test_detect_face_stores_crop_when_face_found(self):
        """detect_face stores the cropped face when FaceLandmarker finds a face."""
        mock_detector = MagicMock(spec=FaceLandmarkerDetector)
        mock_landmarks = make_face_landmarks()
        mock_bbox = (280, 200, 80, 80)
        mock_detector.detect.return_value = (mock_landmarks, mock_bbox)

        face_img, face_mask = make_face_crop()
        mock_cropper = MagicMock(spec=FaceCropper)
        mock_cropper.crop_face.return_value = (face_img, face_mask)

        engine = self._make_engine(mock_detector, mock_cropper)
        bgr_frame = np.full((HEIGHT, WIDTH, 3), (50, 100, 150), dtype=np.uint8)
        rgb_frame = np.full((HEIGHT, WIDTH, 3), (50, 100, 150), dtype=np.uint8)

        engine.detect_face(rgb_frame, bgr_frame)

        assert mock_detector.detect.called
        assert mock_cropper.crop_face.called
        # Verify bbox is passed as keyword arg
        _, kwargs = mock_cropper.crop_face.call_args
        assert kwargs.get("face_bbox") == mock_bbox
        assert engine._face_image is not None
        assert engine._face_mask is not None

    def test_detect_face_clears_crop_when_no_face(self):
        """detect_face clears the face crop when FaceLandmarker finds no face."""
        mock_detector = MagicMock(spec=FaceLandmarkerDetector)
        mock_detector.detect.return_value = (None, None)
        mock_cropper = MagicMock(spec=FaceCropper)
        mock_cropper.crop_face.return_value = None

        engine = self._make_engine(mock_detector, mock_cropper)
        bgr_frame = np.full((HEIGHT, WIDTH, 3), (50, 100, 150), dtype=np.uint8)
        rgb_frame = np.full((HEIGHT, WIDTH, 3), (50, 100, 150), dtype=np.uint8)

        engine._face_image = np.zeros((10, 10, 3), dtype=np.uint8)
        engine._face_mask = np.zeros((10, 10), dtype=np.uint8)

        engine.detect_face(rgb_frame, bgr_frame)

        assert engine._face_image is None
        assert engine._face_mask is None

    def test_jump_detected_during_play(self):
        """A jump gesture triggers the character to jump during PLAYING."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine._player.on_ground is True

        jumping = make_jumping_landmarks(jump_height=80)
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player.on_ground is False

    def test_no_false_jump_when_standing(self):
        """Standing still does not trigger a jump."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        engine.update(standing, MOCK_CONNECTIONS)
        assert engine._player.on_ground is True

    def test_collision_loses_life(self):
        """Character colliding with an obstacle loses a life."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

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
        assert engine.lives == MAX_LIVES - 1
        assert engine.state == MarioGameEngine.PLAYING

    def test_game_over_when_lives_depleted(self):
        """Game over when all lives are lost."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)
        engine.update(standing, MOCK_CONNECTIONS)

        for _ in range(MAX_LIVES):
            obs = MarioObstacle(
                x=CHARACTER_X - 20, ground_y=GROUND_Y,
                width=40, height=100, speed=BASE_SPEED,
                obs_type="block", color=(30, 165, 200),
            )
            engine._obstacle_manager._obstacles = [obs]
            engine.update(standing, MOCK_CONNECTIONS)

        assert engine.lives == 0
        assert engine.state == MarioGameEngine.GAME_OVER

    def test_background_is_sky_color(self):
        """Rendered playing background is light sky-blue (celeste)."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        assert tuple(frame[0, 0]) == SKY_COLOR

    def test_hud_shows_score_level_speed(self):
        """After update in PLAYING, the HUD region is visible."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.handle_key(ord(" "))
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        hud_area = frame[0:80, 0:200]
        assert hud_area.sum() > 0

    def test_render_menu_does_not_crash(self):
        """render() in MENU state renders without errors."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.render(frame, MOCK_CONNECTIONS)

    def test_render_playing_does_not_crash(self):
        """render() in PLAYING state renders without errors."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.handle_key(ord(" "))
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

    def test_render_game_over_does_not_crash(self):
        """render() in GAME_OVER state renders without errors."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.handle_key(ord(" "))
        engine._state = MarioGameEngine.GAME_OVER
        engine.render(frame, MOCK_CONNECTIONS)

    def test_reset_from_game_over_to_playing(self):
        """handle_key(SPACE) from GAME_OVER restarts the game."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))
        engine._state = MarioGameEngine.GAME_OVER
        engine.handle_key(ord(" "))
        assert engine.state == MarioGameEngine.PLAYING
        assert engine.level == 1

    def test_handle_key_q_does_not_start(self):
        """Pressing 'q' from MENU does not start the game."""
        engine = self._make_engine()
        engine.handle_key(ord("q"))
        assert engine.state == MarioGameEngine.MENU

    def test_level_progression(self):
        """Level increments every 5 obstacles passed."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        engine._obstacle_manager._passed_count = 5
        assert engine.level == 2

        engine._obstacle_manager._passed_count = 10
        assert engine.level == 3

    def test_speed_progression(self):
        """Speed uses the additive multiplier BASE_SPEED * (1 + 0.1*(level-1))."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        engine._obstacle_manager._passed_count = 0
        assert engine.speed == pytest.approx(BASE_SPEED)

        engine._obstacle_manager._passed_count = 5
        assert engine.speed == pytest.approx(BASE_SPEED * (1 + SPEED_INCREMENT))

        engine._obstacle_manager._passed_count = 10
        assert engine.speed == pytest.approx(BASE_SPEED * (1 + 2 * SPEED_INCREMENT))

    def test_spawn_gap_at_level_1_is_wide(self):
        """Level 1 spawn gap range is wide (180-280 frames)."""
        engine = self._make_engine()
        gap = engine._obstacle_manager.spawn_gap_range
        assert gap == (180, 280)

    def test_sky_block_spawns_one_per_level_up(self):
        """Reaching level 2 (5 obstacles) spawns exactly one sky block."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        assert len(engine._sky_blocks) == 0

        engine._obstacle_manager._passed_count = 5
        engine._update_sky_blocks(engine.speed)
        assert engine.level == 2
        assert len(engine._sky_blocks) == 1

        # No further spawn without a new level milestone
        engine._update_sky_blocks(engine.speed)
        assert len(engine._sky_blocks) == 1

    def test_collecting_sky_block_grants_coin_not_life(self):
        """Collecting a sky block adds +1 coin and never a life."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)

        engine._obstacle_manager._passed_count = 5
        engine._update_sky_blocks(engine.speed)
        assert len(engine._sky_blocks) == 1

        block = engine._sky_blocks[0]
        bbox = engine._player.bounding_box
        block.x, block.y = bbox[0], bbox[1]
        block.size = max(block.size, bbox[2] + 1, bbox[3] + 1)

        lives_before = engine.lives
        coins_before = engine.coins
        engine._update_sky_blocks(engine.speed)

        assert engine.coins == coins_before + 1
        assert engine.lives == lives_before
        assert block.collected is True

    def test_cloud_render_uses_sprite(self):
        """Cloud.render with a sprite differs from the ellipse; no sprite keeps it."""
        sprite = np.zeros((10, 10, 4), dtype=np.uint8)
        sprite[2:8, 2:8, :3] = 255
        sprite[2:8, 2:8, 3] = 255

        with_sprite = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        without = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        reference = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        Cloud(x=100, y=100, width=80, height=60, sprite=sprite).render(with_sprite)
        Cloud(x=100, y=100, width=80, height=60).render(without)
        cv2.ellipse(reference, (140, 130), (40, 30), 0, 0, 360, CLOUD_COLOR, -1)

        assert not np.array_equal(with_sprite, without)
        assert np.array_equal(without, reference)

    def test_double_jump_detected_during_play(self):
        """A second jump gesture while airborne triggers a double jump."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        standing = make_standing_landmarks()
        engine.update(standing, MOCK_CONNECTIONS)

        jumping = make_jumping_landmarks(jump_height=80)
        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player._jump_count == 1

        for _ in range(JUMP_COOLDOWN + 2):
            engine.update(standing, MOCK_CONNECTIONS)

        engine.update(jumping, MOCK_CONNECTIONS)
        assert engine._player._jump_count == 2

    def test_obstacle_types(self):
        """OBSTACLE_TYPES contains pipe, block, and goomba."""
        assert set(OBSTACLE_TYPES) == {"pipe", "block", "goomba"}

    def test_update_requires_bgr_frame_arg(self):
        """update() accepts bgr_frame as third argument."""
        engine = self._make_engine()
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS, frame)
        # Should not raise

    def test_render_game_with_face_overlay(self):
        """Playing render with face crop draws face overlay without crashing."""
        mock_detector = MagicMock(spec=FaceLandmarkerDetector)
        mock_detector.detect.return_value = (make_face_landmarks(), (280, 200, 80, 80))
        mock_cropper = MagicMock(spec=FaceCropper)
        face_img, face_mask = make_face_crop()
        mock_cropper.crop_face.return_value = (face_img, face_mask)

        engine = MarioFaceGameEngine(
            WIDTH, HEIGHT, MagicMock(), mock_detector, mock_cropper,
        )
        engine.handle_key(ord(" "))

        bgr_frame = np.full((HEIGHT, WIDTH, 3), (50, 100, 150), dtype=np.uint8)
        rgb_frame = np.full((HEIGHT, WIDTH, 3), (50, 100, 150), dtype=np.uint8)
        engine.detect_face(rgb_frame, bgr_frame)

        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS, bgr_frame)
        engine.render(frame, MOCK_CONNECTIONS)

        # Frame should have content (face overlay + body + HUD)
        assert frame.sum() > 0

    def test_graffiti_drawn_on_bricks_with_graffiti_y(self):
        """_render_static_environment(graffiti_y) draws graffiti below ground_y."""
        engine = self._make_engine()
        frame = np.full((HEIGHT, WIDTH, 3), SKY_COLOR, dtype=np.uint8)
        engine._render_static_environment(
            frame, draw_clouds=False,
            graffiti_y=GROUND_Y + GRAFFITI_BRICK_Y_OFFSET,
        )

        region = frame[GROUND_Y + 1:GROUND_Y + 30, WIDTH // 2 - 110:WIDTH // 2 + 110]
        bright = (region >= 250).all(axis=2)
        assert bright.sum() > 0

    def test_graffiti_default_position_above_ground(self):
        """Default _render_static_environment keeps graffiti above the ground."""
        engine = self._make_engine()
        frame = np.full((HEIGHT, WIDTH, 3), SKY_COLOR, dtype=np.uint8)
        engine._render_static_environment(frame, draw_clouds=False)

        region = frame[GROUND_Y:HEIGHT, WIDTH // 2 - 110:WIDTH // 2 + 110]
        bright = (region >= 250).all(axis=2)
        assert bright.sum() == 0

    def test_spawned_clouds_are_wider_than_tall(self):
        """Spawned clouds keep a wide cloud-like proportion (height < width)."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))
        engine._spawn_cloud(engine.speed)
        engine._spawn_cloud(engine.speed)

        assert len(engine._clouds) >= 1
        for cloud in engine._clouds:
            assert cloud.height < cloud.width
            assert cloud.height == max(cloud.width // 4, 8)

    def test_seeded_clouds_are_wider_than_tall(self):
        """Clouds seeded on reset keep a wide proportion."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        assert len(engine._clouds) > 0
        for cloud in engine._clouds:
            assert cloud.height < cloud.width

    def test_face_preview_drawn_with_face(self):
        """Playing render with a face draws the preview in the lower-right corner."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        face_img = np.full((50, 50, 3), (0, 0, 255), dtype=np.uint8)
        mask = np.zeros((50, 50), dtype=np.uint8)
        cv2.circle(mask, (25, 25), 25, 255, -1)
        engine._face_image = face_img
        engine._face_mask = mask

        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        # Preview blends the red face into the brick band at the lower-right
        px = frame[GROUND_Y + 30, WIDTH - 35]
        assert px[2] > 100 and px[2] > px[1]

    def test_face_preview_outline_when_no_face(self):
        """Playing render without a face draws only the preview circle outline."""
        engine = self._make_engine()
        engine.handle_key(ord(" "))

        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        engine.update(make_standing_landmarks(), MOCK_CONNECTIONS)
        engine.render(frame, MOCK_CONNECTIONS)

        region = frame[GROUND_Y + 5:GROUND_Y + 60, WIDTH - 60:WIDTH - 5]
        bright = region.sum(axis=2) > 600
        assert bright.sum() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
