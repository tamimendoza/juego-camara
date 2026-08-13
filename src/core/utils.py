"""Utility functions for pose landmark processing and body part mapping."""

from typing import List, Optional, Tuple

import numpy as np

PixelPoint = Tuple[int, int]
LandmarkPoint = Optional[PixelPoint]  # None when landmark is not visible


def normalized_to_pixel(
    x: float, y: float, width: int, height: int
) -> PixelPoint:
    """Convert MediaPipe normalized coordinates (0-1) to pixel coordinates."""
    px = int(x * width)
    py = int(y * height)
    return (
        max(0, min(px, width - 1)),
        max(0, min(py, height - 1)),
    )


def landmarks_to_pixels(
    landmarks, width: int, height: int, visibility_threshold: float = 0.5
) -> List[LandmarkPoint]:
    """Convert MediaPipe landmarks to pixel coordinates.

    Returns None for landmarks whose visibility or presence is below the
    threshold.  ``PoseLandmarker`` results use ``presence`` (whether the
    landmark is within scene bounds); ``mp.solutions.pose`` results use
    ``visibility``.  Both are checked — a None value is ignored.
    """
    points: List[LandmarkPoint] = []
    for lm in landmarks:
        if _is_occluded(lm, visibility_threshold):
            points.append(None)
        else:
            points.append(normalized_to_pixel(lm.x, lm.y, width, height))
    return points


def _is_occluded(lm, threshold: float = 0.5) -> bool:
    """Check if a landmark is occluded or not present.

    Checks both ``presence`` (within scene bounds) and ``visibility``
    (not occluded by other objects).  Either field below *threshold*
    causes the landmark to be considered hidden.  Fields that are
    ``None`` are ignored.
    """
    presence = getattr(lm, "presence", None)
    if presence is not None and presence < threshold:
        return True
    visibility = getattr(lm, "visibility", None)
    if visibility is not None and visibility < threshold:
        return True
    return False


def rgb_to_mp_image(rgb_array: np.ndarray):
    """Convert an RGB numpy array to a MediaPipe Image.

    Used before passing frames to ``PoseLandmarker.detect_for_video()``.
    """
    import mediapipe as mp
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_array)


def mp_image_to_numpy(image) -> np.ndarray:
    """Convert a MediaPipe Image to a numpy array (RGB or single-channel)."""
    return np.array(image.numpy_view())


def smooth_landmarks(
    prev_points: Optional[List[LandmarkPoint]],
    curr_points: List[LandmarkPoint],
    alpha: float = 0.3,
) -> List[LandmarkPoint]:
    """Apply exponential moving average to landmark points.

    alpha=0.3 gives 30% weight to the current frame, 70% to the previous.
    Points that are None in either frame fall back to the available value.
    """
    if prev_points is None:
        return list(curr_points)
    smoothed: List[LandmarkPoint] = []
    for prev, curr in zip(prev_points, curr_points):
        if prev is None:
            smoothed.append(curr)
        elif curr is None:
            smoothed.append(prev)
        else:
            sx = int(prev[0] * (1 - alpha) + curr[0] * alpha)
            sy = int(prev[1] * (1 - alpha) + curr[1] * alpha)
            smoothed.append((sx, sy))
    return smoothed


def get_visible_polygon(
    points: List[LandmarkPoint], indices: List[int]
) -> Optional[List[PixelPoint]]:
    """Return pixel coordinates for the given landmark indices.

    Returns None if any required index is None (occluded), so the
    caller can skip drawing that polygon.
    """
    polygon = []
    for i in indices:
        if i >= len(points) or points[i] is None:
            return None
        polygon.append(points[i])
    return polygon


# MediaPipe Pose landmark index groups (33 total landmarks)
# Head (0-10): nose, eyes (inner/outer), ears, mouth corners
# Arms (11-22): shoulders, elbows, wrists, pinkies, index, thumbs
# Torso (11,12,23,24): shoulders + hips
# Legs (23-32): hips, knees, ankles, heels, foot indices
BODY_PART_GROUPS = {
    "head": [[0, 2, 5, 7, 8, 10, 9, 1], [0, 3, 4, 6]],
    "torso": [11, 12, 24, 23],
    "left_arm": [11, 13, 15, 21, 19, 17],
    "right_arm": [12, 14, 16, 22, 20, 18],
    "left_leg": [23, 25, 27, 31, 29],
    "right_leg": [24, 26, 28, 32, 30],
}

# Simplified triangle polygons for limbs (shoulder/elbow/wrist)
LIMB_TRIANGLES = {
    "left_upper_arm": [11, 13, 15],
    "right_upper_arm": [12, 14, 16],
    "left_forearm": [13, 15, 19],  # elbow, wrist, index
    "right_forearm": [14, 16, 20],
    "left_thigh": [23, 25, 27],
    "right_thigh": [24, 26, 28],
    "left_calf": [25, 27, 29],  # knee, ankle, heel
    "right_calf": [26, 28, 30],
}
