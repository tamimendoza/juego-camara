"""Pose landmark mirroring helper used by the 2D game framework.

Mirroring makes the on-screen miniatura behave like the player's mirror
image: an arm pointing forward along the character's path stays forward,
instead of being rendered in reverse.
"""

from typing import List, Sequence

from .utils import LandmarkPoint


# Symmetric left/right landmark index pairs for mirror mode.
# In a real mirror left and right are swapped; the X-flip is applied on top
# so that limb directions are preserved relative to the body centerline.
# Head/face landmarks (0–10) are intentionally omitted — they are
# midline or asymmetric and only get X-flipped.
_MIRROR_LANDMARK_MAP: dict = {
    11: 12, 12: 11,   # shoulders
    13: 14, 14: 13,   # elbows
    15: 16, 16: 15,   # wrists
    17: 18, 18: 17,   # pinkies
    19: 20, 20: 19,   # index fingers
    21: 22, 22: 21,   # thumbs
    23: 24, 24: 23,   # hips
    25: 26, 26: 25,   # knees
    27: 28, 28: 27,   # ankles
    29: 30, 30: 29,   # heels
    31: 32, 32: 31,   # foot indices
}


def mirror_points(points: Sequence[LandmarkPoint], width: int) -> List[LandmarkPoint]:
    """Mirror landmark points horizontally for mirror mode.

    Swaps symmetric left/right landmark indices *first*, then X-flips the
    coordinates. This preserves limb direction relative to the body centerline
    (e.g., an arm extended backward stays backward in the mirrored character),
    matching real-mirror behavior rather than reversing every direction.
    """
    mirrored: List[LandmarkPoint] = []
    for i in range(len(points)):
        source = _MIRROR_LANDMARK_MAP.get(i, i)
        if source >= len(points):
            mirrored.append(None)
            continue
        p = points[source]
        if p is None:
            mirrored.append(None)
        else:
            mirrored.append((width - p[0], p[1]))
    return mirrored