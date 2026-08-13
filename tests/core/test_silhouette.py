"""Unit tests for SilhouetteDrawer rendering methods."""

import cv2
import numpy as np
import pytest

from src.core.silhouette import SilhouetteDrawer


class TestDrawHeadCircle:
    def test_draws_circle_at_nose(self):
        """Head circle is centered at the nose landmark and filled white."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # nose at center, shoulders 80px apart horizontally
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (280, 300)  # left shoulder
        points[12] = (360, 300)  # right shoulder

        drawer.draw_head_circle(frame, points)

        # shoulder_width = 80, radius = max(80*0.25, 10) = 20
        # center pixel should be white (255, 255, 255)
        pixel = frame[240, 320]
        assert pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255

    def test_does_not_draw_when_nose_missing(self):
        """No circle drawn if nose (index 0) is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (280, 300)
        points[12] = (360, 300)

        drawer.draw_head_circle(frame, points)

        assert frame.sum() == 0

    def test_does_not_draw_when_shoulder_missing(self):
        """No circle drawn if either shoulder (11 or 12) is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)

        drawer.draw_head_circle(frame, points)

        assert frame.sum() == 0

    def test_radius_scales_with_shoulder_width(self):
        """Larger shoulder width produces a larger circle."""
        drawer = SilhouetteDrawer()

        # Wide shoulders
        frame_wide = np.zeros((480, 640, 3), dtype=np.uint8)
        points_wide = [None] * 33
        points_wide[0] = (320, 240)
        points_wide[11] = (120, 300)
        points_wide[12] = (520, 300)
        drawer.draw_head_circle(frame_wide, points_wide)

        # Narrow shoulders
        frame_narrow = np.zeros((480, 640, 3), dtype=np.uint8)
        points_narrow = [None] * 33
        points_narrow[0] = (320, 240)
        points_narrow[11] = (300, 300)
        points_narrow[12] = (340, 300)
        drawer.draw_head_circle(frame_narrow, points_narrow)

        # Wide shoulders should produce more filled pixels than narrow
        assert frame_wide.sum() > frame_narrow.sum()

    def test_minimum_radius_clamped(self):
        """When shoulder width is very small, minimum radius of 10 is used."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)
        points[11] = (319, 300)  # shoulder_width = 2, radius = max(0, 10) = 10
        points[12] = (321, 300)

        drawer.draw_head_circle(frame, points)

        # Pixel 5 away from center is inside the circle (radius 10)
        assert frame[240, 325, 0] == 255
        # Pixel 15 away from center is outside the circle
        assert frame[240, 335, 0] == 0


class TestDrawBodyLines:
    def test_draws_body_connections(self):
        """Body connections (both indices >= 11) are drawn as lines."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (100, 100)  # left shoulder
        points[12] = (200, 100)  # right shoulder
        points[14] = (200, 200)  # right elbow
        connections = [(11, 12), (12, 14), (0, 1)]

        drawer.draw_body_lines(frame, points, connections)

        # Body line (11,12): horizontal at y=100 between x=100 and x=200
        assert frame[100, 150, 0] != 0
        # Body line (12,14): vertical at x=200 between y=100 and y=200
        assert frame[150, 200, 0] != 0

    def test_excludes_face_connections(self):
        """Face connections (either index < 11) are not drawn."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (50, 50)    # nose
        points[1] = (40, 40)    # left eye inner
        points[11] = (100, 100)  # left shoulder
        points[12] = (200, 100)  # right shoulder
        connections = [(0, 1), (11, 12)]

        drawer.draw_body_lines(frame, points, connections)

        # Face connection (0,1) should NOT be drawn
        assert frame[45, 45, 0] == 0
        # Body connection (11,12) SHOULD be drawn
        assert frame[100, 150, 0] != 0

    def test_skips_none_points(self):
        """Connections to None landmarks are skipped."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (100, 100)
        points[12] = None  # not visible
        connections = [(11, 12)]

        drawer.draw_body_lines(frame, points, connections)

        assert frame.sum() == 0

    def test_skips_out_of_range_connections(self):
        """Connections referencing indices beyond the points list are skipped."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [(10, 10)] * 33
        connections = [(11, 35)]  # index 35 out of range

        drawer.draw_body_lines(frame, points, connections)

        assert frame.sum() == 0

    def test_empty_connections(self):
        """Empty connections list produces no drawing."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [(10, 10)] * 33
        connections = []

        drawer.draw_body_lines(frame, points, connections)

        assert frame.sum() == 0


class TestRenderCharacterHeadCircleStyle:
    def test_style_5_blank_head_circle_body_lines(self):
        """Style 5 renders head circle + body lines on solid black background."""
        drawer = SilhouetteDrawer()
        frame = np.full((480, 640, 3), 255, dtype=np.uint8)  # start white
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (280, 340)  # left shoulder
        points[12] = (360, 340)  # right shoulder
        connections = [(0, 1), (11, 12)]  # face + body

        drawer.render_character(
            frame, points, connections=connections,
            styles=["blank", "head_circle", "body_lines"],
        )

        # Background should be solid black (blank)
        assert frame[0, 0, 0] == 0  # top-left corner is black

        # Head circle should be white at nose position
        assert frame[240, 320, 0] == 255

        # Body line (11,12) should be gray at midpoint
        assert frame[340, 320, 0] != 0

        # Face connection (0,1) should NOT be drawn
        assert frame[0, 0, 0] == 0


class TestDrawMarioHead:
    def test_draws_face_and_cap(self):
        """Mario head draws a peach face circle and a red cap above it."""
        from src.core.silhouette import MARIO_FACE, MARIO_HAT

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (280, 300)  # left shoulder
        points[12] = (360, 300)  # right shoulder

        drawer.draw_mario_head(frame, points)

        # Face center pixel should be peach (MARIO_FACE)
        face_pixel = frame[240, 320]
        assert tuple(face_pixel) == MARIO_FACE

        # Cap should be red somewhere above the face center.
        # nose_y=240, radius=20 → cap center at y=220; cap ellipse spans roughly
        # y=210–230. Check a vertical scan above the face.
        found_cap = False
        for y in range(210, 235):
            if tuple(frame[y, 320]) == MARIO_HAT:
                found_cap = True
                break
        assert found_cap, "No red cap pixel found above the face"

    def test_does_not_draw_when_nose_missing(self):
        """No Mario head if nose (index 0) is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (280, 300)
        points[12] = (360, 300)

        drawer.draw_mario_head(frame, points)
        assert frame.sum() == 0

    def test_does_not_draw_when_shoulder_missing(self):
        """No Mario head if either shoulder is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)

        drawer.draw_mario_head(frame, points)
        assert frame.sum() == 0


class TestDrawMarioBody:
    def test_draws_body_connections(self):
        """Mario body draws shoulder and leg connections in Mario colors."""
        from src.core.silhouette import MARIO_SHIRT, MARIO_OVERALL

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (100, 100)   # left shoulder
        points[12] = (200, 100)   # right shoulder
        points[14] = (200, 200)   # right elbow
        points[24] = (200, 300)   # right hip
        points[26] = (200, 400)   # right knee
        points[30] = (200, 450)   # right ankle
        connections = [(11, 12), (12, 14), (12, 24), (24, 26), (26, 30), (0, 1)]

        drawer.draw_mario_body(frame, points, connections)

        # Shoulder line (11,12) — both >= 11, < 23 → red shirt
        assert tuple(frame[100, 150]) == MARIO_SHIRT
        # Arm line (12,14) — both in 11–22 → red shirt
        assert tuple(frame[150, 200]) == MARIO_SHIRT
        # Leg line (24,26) — both >= 23 → blue overall
        assert tuple(frame[350, 200]) == MARIO_OVERALL

    def test_excludes_face_connections(self):
        """Face connections (either index < 11) are not drawn."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (50, 50)
        points[1] = (40, 40)
        points[11] = (100, 100)
        points[12] = (200, 100)
        connections = [(0, 1), (11, 12)]

        drawer.draw_mario_body(frame, points, connections)

        # Face connection (0,1) should NOT be drawn
        assert frame.sum() == 0 or frame[45, 45].any() == False  # no face pixels
        # Body connection (11,12) SHOULD be drawn
        assert frame[100, 150].any() != 0

    def test_skips_none_points(self):
        """Connections to None landmarks are skipped."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (100, 100)
        connections = [(11, 12)]

        drawer.draw_mario_body(frame, points, connections)
        assert frame.sum() == 0

    def test_render_character_with_mario_styles(self):
        """render_character with mario_head + mario_body styles draws Mario look."""
        from src.core.silhouette import MARIO_FACE, MARIO_HAT, MARIO_SHIRT, MARIO_OVERALL

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (300, 300)  # left shoulder
        points[12] = (340, 300)  # right shoulder
        points[14] = (340, 340)  # right elbow
        points[24] = (320, 360)  # right hip
        points[26] = (320, 400)  # right knee
        points[30] = (320, 440)  # right ankle
        connections = [(11, 12), (12, 14), (12, 24), (24, 26), (26, 30)]

        drawer.render_character(
            frame, points, connections=connections,
            styles=["mario_head", "mario_body"],
        )

        # Face should be peach
        assert tuple(frame[240, 320]) == MARIO_FACE
        # Cap above face should be red (scan a few pixels above the nose for the cap arc)
        found_cap = False
        for y in range(215, 235):
            if tuple(frame[y, 320]) == MARIO_HAT:
                found_cap = True
                break
        assert found_cap, "No red cap pixel found above the face"
        # Shirt line (11,12) at y=300 between x=300 and x=340 should be red
        assert tuple(frame[300, 320]) == MARIO_SHIRT


class TestDrawMinecraftHead:
    def test_draws_cap_and_face_blocks(self):
        """Minecraft head renders a red cap block above a peach face block."""
        from src.core.silhouette import MARIO_FACE, MARIO_HAT

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (280, 300)  # left shoulder
        points[12] = (360, 300)  # right shoulder

        drawer.draw_minecraft_head(frame, points)

        # Face center should be peach
        assert tuple(frame[240, 320]) == MARIO_FACE

        # Cap block should be red somewhere above the face center.
        # nose_y=240, block ~40px, cap_h ~14 → cap from y=220 to y=234
        found_cap = False
        for y in range(215, 240):
            if tuple(frame[y, 320]) == MARIO_HAT:
                found_cap = True
                break
        assert found_cap, "No red cap pixel found above the face"

    def test_draws_pixel_eyes(self):
        """Minecraft head has two small black pixel eyes in the face block."""
        from src.core.silhouette import MC_EYE

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)
        points[11] = (280, 300)
        points[12] = (360, 300)

        drawer.draw_minecraft_head(frame, points)

        # Eyes should be black pixels in the face area (below cap, around nose x)
        # Scan a horizontal band below the cap for black pixels
        found_eye = False
        cap_h_estimate = 14  # block_size ~40 * 0.35
        eye_band_start = 240 + cap_h_estimate
        for y in range(eye_band_start, eye_band_start + 25):
            for x in range(300, 340):
                if tuple(frame[y, x]) == MC_EYE:
                    found_eye = True
                    break
            if found_eye:
                break
        assert found_eye, "No pixel eyes found in the face block"

    def test_block_border_drawn(self):
        """Minecraft head has a dark border outlining the square block."""
        from src.core.silhouette import MC_BLOCK_BORDER

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)
        points[11] = (280, 300)
        points[12] = (360, 300)

        drawer.draw_minecraft_head(frame, points)

        # The block has a dark border; check that border pixels exist
        # near the corners of where the head block should be
        # block_size = max(100 * 0.5, 20) = 40, half = 20
        # Head block from (300, 220) to (340, 260)
        assert tuple(frame[220, 300]) == MC_BLOCK_BORDER or \
               tuple(frame[220, 340]) == MC_BLOCK_BORDER or \
               tuple(frame[260, 300]) == MC_BLOCK_BORDER or \
               tuple(frame[260, 340]) == MC_BLOCK_BORDER

    def test_does_not_draw_when_nose_missing(self):
        """No Minecraft head if nose (index 0) is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (280, 300)
        points[12] = (360, 300)

        drawer.draw_minecraft_head(frame, points)
        assert frame.sum() == 0


class TestDrawMinecraftBody:
    def test_draws_body_as_solid_rectangles(self):
        """Minecraft body draws five solid rectangle blocks via predefined segments."""
        from src.core.silhouette import MARIO_SHIRT, MARIO_OVERALL

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (300, 200)   # left shoulder
        points[12] = (340, 200)   # right shoulder
        points[15] = (280, 280)   # left wrist
        points[16] = (360, 280)   # right wrist
        points[23] = (300, 300)   # left hip
        points[24] = (340, 300)   # right hip
        points[27] = (300, 400)   # left heel
        points[28] = (340, 400)   # right heel
        connections = [(11, 12)]  # connections are NOT used for body rendering

        drawer.draw_minecraft_body(frame, points, connections)

        # Should have red pixels (shirt: torso + arms)
        red_pixels = np.all(frame == np.array(MARIO_SHIRT).reshape(1, 1, 3), axis=2)
        assert red_pixels.sum() > 0
        # Should have blue pixels (overalls: legs)
        blue_pixels = np.all(frame == np.array(MARIO_OVERALL).reshape(1, 1, 3), axis=2)
        assert blue_pixels.sum() > 0

    def test_excludes_face_landmarks(self):
        """Face landmarks (0–10) do not produce body block drawing."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (50, 50)      # nose (face)
        points[1] = (40, 40)      # face
        points[11] = (100, 100)   # left shoulder
        points[12] = (200, 100)   # right shoulder
        points[15] = (80, 200)    # left wrist
        points[16] = (220, 200)   # right wrist
        points[23] = (100, 200)   # left hip
        points[24] = (200, 200)   # right hip
        points[27] = (100, 350)   # left heel
        points[28] = (200, 350)   # right heel
        connections = [(0, 1)]

        drawer.draw_minecraft_body(frame, points, connections)

        # Face landmarks should not be drawn
        assert tuple(frame[45, 45]) == (0, 0, 0)
        # Body blocks should be drawn
        assert frame.sum() > 0

    def test_skips_none_segments(self):
        """Limb blocks are skipped when required landmarks are None."""
        from src.core.silhouette import MARIO_SHIRT, MARIO_OVERALL

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (100, 100)   # left shoulder
        points[12] = (200, 100)   # right shoulder
        # No wrists, hips, or heels → only torso can't draw (needs hips too)
        # So nothing should be drawn
        drawer.draw_minecraft_body(frame, points, [])
        assert frame.sum() == 0

        # Now add hips + heels → torso and legs draw, but arms can't (no wrists)
        points[23] = (100, 200)   # left hip
        points[24] = (200, 200)   # right hip
        points[27] = (100, 350)   # left heel
        points[28] = (200, 350)   # right heel
        drawer.draw_minecraft_body(frame, points, [])
        # Torso (red) + legs (blue) should be drawn, but no arms
        red_pixels = np.all(frame == np.array(MARIO_SHIRT).reshape(1, 1, 3), axis=2)
        assert red_pixels.sum() > 0  # torso is red
        blue_pixels = np.all(frame == np.array(MARIO_OVERALL).reshape(1, 1, 3), axis=2)
        assert blue_pixels.sum() > 0  # legs are blue

    def test_render_character_with_minecraft_styles(self):
        """render_character with minecraft_head + minecraft_body draws voxel Mario."""
        from src.core.silhouette import MARIO_FACE, MARIO_HAT

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (300, 300)  # left shoulder
        points[12] = (340, 300)  # right shoulder
        points[15] = (280, 340)  # left wrist
        points[16] = (360, 340)  # right wrist
        points[23] = (300, 340)  # left hip
        points[24] = (340, 340)  # right hip
        points[27] = (300, 380)  # left heel
        points[28] = (340, 380)  # right heel
        connections = [(11, 12), (12, 24), (24, 28)]

        drawer.render_character(
            frame, points, connections=connections,
            styles=["minecraft_head", "minecraft_body"],
        )

        # Face should be peach
        assert tuple(frame[240, 320]) == MARIO_FACE
        # Should have red pixels (cap/shirt blocks)
        assert frame.sum() > 0


class TestDrawOrientedRect:
    def test_draws_rectangle_between_two_points(self):
        """_draw_oriented_rect fills a thick rectangle along the given line."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        drawer._draw_oriented_rect(frame, (100, 100), (200, 100), width=10,
                                   color=(0, 0, 255))

        # Midpoint should be filled (color (0,0,255) = Red, BGR channel 2)
        assert frame[100, 150, 2] == 255
        # Pixels above and below the line (within half-width) should also be filled
        assert frame[95, 150, 2] == 255  # 5px above
        assert frame[105, 150, 2] == 255  # 5px below

    def test_draws_vertical_rectangle(self):
        """_draw_oriented_rect works for vertical lines."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        drawer._draw_oriented_rect(frame, (320, 100), (320, 300), width=10,
                                   color=(0, 255, 0))

        assert frame[200, 320, 1] == 255  # green
        assert frame[200, 325, 1] == 255  # 5px to the right
        assert frame[200, 315, 1] == 255  # 5px to the left

    def test_skips_none_points(self):
        """_draw_oriented_rect skips when either point is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        drawer._draw_oriented_rect(frame, None, (200, 100), width=10,
                                   color=(0, 0, 255))
        assert frame.sum() == 0

    def test_draws_border(self):
        """_draw_oriented_rect draws a border polyline when border is given."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        drawer._draw_oriented_rect(frame, (100, 100), (200, 100), width=10,
                                   color=(0, 0, 255),
                                   border=(20, 20, 20))

        # Border should be visible at the edges of the rectangle
        assert tuple(frame[95, 100]) == (20, 20, 20) or \
               tuple(frame[105, 100]) == (20, 20, 20)


class TestDrawFaceOverlay:
    def test_draws_face_image_at_nose(self):
        """Face overlay places the face crop centered at the nose landmark."""
        from src.core.silhouette import MARIO_SHIRT

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (280, 300)  # left shoulder
        points[12] = (360, 300)  # right shoulder

        # shoulder_width = 80, radius = max(80*0.25, 10) = 20
        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        face_mask = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(face_mask, (20, 20), 20, 255, -1)

        drawer.draw_face_overlay(frame, points, face_img, face_mask)

        # The face center pixel should now show the face image color
        assert tuple(frame[240, 320]) == (100, 150, 200)

    def test_falls_back_to_peach_face_circle_when_no_face(self):
        """When face_image is None, falls back to peach face circle."""
        from src.core.silhouette import MARIO_FACE

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)   # nose
        points[11] = (280, 300)  # left shoulder
        points[12] = (360, 300)  # right shoulder

        drawer.draw_face_overlay(frame, points, face_image=None, face_mask=None)

        # Should draw peach face circle at nose
        assert tuple(frame[240, 320]) == MARIO_FACE

    def test_falls_back_to_peach_face_circle_when_no_mask(self):
        """When face_mask is None but face_image exists, falls back to peach circle."""
        from src.core.silhouette import MARIO_FACE

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)
        points[11] = (280, 300)
        points[12] = (360, 300)

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        drawer.draw_face_overlay(frame, points, face_img, face_mask=None)

        assert tuple(frame[240, 320]) == MARIO_FACE

    def test_does_not_draw_when_nose_missing(self):
        """No face overlay drawn if nose (index 0) is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[11] = (280, 300)
        points[12] = (360, 300)

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        face_mask = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(face_mask, (20, 20), 20, 255, -1)

        drawer.draw_face_overlay(frame, points, face_img, face_mask)
        assert frame.sum() == 0

    def test_does_not_draw_when_shoulder_missing(self):
        """No face overlay drawn if either shoulder is None."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        face_mask = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(face_mask, (20, 20), 20, 255, -1)

        drawer.draw_face_overlay(frame, points, face_img, face_mask)
        assert frame.sum() == 0

    def test_face_overlay_resizes_to_shoulder_radius(self):
        """Face image is resized to match the shoulder-based head radius."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)
        points[11] = (240, 300)  # shoulder_width = 160, radius = 40
        points[12] = (400, 300)

        # Small face image that should be resized up to 80x80 (radius 40)
        face_img = np.full((10, 10, 3), (50, 100, 150), dtype=np.uint8)
        face_mask = np.full((10, 10), 255, dtype=np.uint8)

        drawer.draw_face_overlay(frame, points, face_img, face_mask)

        # Center pixel should be the face color (resized up)
        assert tuple(frame[240, 320]) == (50, 100, 150)


class TestRenderCharacterFaceOverlayStyle:
    def test_face_overlay_style_draws_face_image(self):
        """render_character with 'face_overlay' style overlays the face image."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)
        points[11] = (280, 300)
        points[12] = (360, 300)
        points[14] = (360, 340)  # right elbow (body line)
        connections = [(11, 12), (12, 14)]

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        face_mask = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(face_mask, (20, 20), 20, 255, -1)

        drawer.render_character(
            frame, points, connections=connections,
            styles=["mario_body", "face_overlay"],
            face_image=face_img, face_mask=face_mask,
        )

        # Face overlay should be drawn at the nose position
        assert tuple(frame[240, 320]) == (100, 150, 200)
        # Body line should also be drawn (red shirt)
        from src.core.silhouette import MARIO_SHIRT
        assert tuple(frame[300, 320]) == MARIO_SHIRT

    def test_face_overlay_style_without_face_falls_back(self):
        """render_character with 'face_overlay' but no face image draws peach fallback."""
        from src.core.silhouette import MARIO_FACE

        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)
        points[11] = (280, 300)
        points[12] = (360, 300)
        connections = [(11, 12)]

        drawer.render_character(
            frame, points, connections=connections,
            styles=["mario_body", "face_overlay"],
        )

        # Should fall back to peach face circle at the nose
        assert tuple(frame[240, 320]) == MARIO_FACE

    def test_face_overlay_with_body_lines_excludes_face_connections(self):
        """Face connections are not drawn as skeleton lines in face_overlay mode."""
        drawer = SilhouetteDrawer()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        points = [None] * 33
        points[0] = (320, 240)   # nose (center of face circle, radius=20)
        points[1] = (320, 200)   # left eye inner (above face circle)
        points[11] = (280, 300)  # left shoulder
        points[12] = (360, 300)  # right shoulder
        connections = [(0, 1), (11, 12)]  # face connection + body connection

        face_img = np.full((40, 40, 3), (100, 150, 200), dtype=np.uint8)
        face_mask = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(face_mask, (20, 20), 20, 255, -1)

        drawer.render_character(
            frame, points, connections=connections,
            styles=["mario_body", "face_overlay"],
            face_image=face_img, face_mask=face_mask,
        )

        # Face connection (0,1) should NOT be drawn as a skeleton line.
        # Point (320, 210) is on the line from (320,240) to (320,200) but
        # outside the face circle (radius 20 from nose at 240), so it should
        # be zero if face connections are properly excluded.
        assert frame[210, 320].sum() == 0
        # Body connection (11,12) SHOULD be drawn
        assert frame[300, 320].sum() > 0
