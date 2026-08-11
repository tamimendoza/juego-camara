"""Mario Face Jump game entry point: webcam pose + face-capture jumping game.

Pipeline:
    camera.read_frame -> BGR->RGB conversion -> mp.Image -> PoseLandmarker.detect ->
    FaceMesh.detect -> FaceCropper.crop_face -> landmark extraction ->
    MarioFaceGameEngine.update -> MarioFaceGameEngine.render -> display

The player's real face (captured from the webcam via MediaPipe FaceMesh) replaces
the Mario character's head entirely. The character still mimics the player's pose
and jump via PoseLandmarker body landmarks, but the head is a real face crop
instead of a peach face circle + cap + hair arc. The Mario body lines (red shirt
for arms/torso, blue overalls for legs) are preserved.

The player jumps by physically raising above their standing baseline. Obstacles
(pipes, blocks, goombas) start widely separated and tighten every 5 obstacles
passed. Every 5 obstacles cleared, the player levels up; from level 2, speed
increases 10% per level. The player has 3 lives.

Usage:
    python3 -m src.mario_face_main
    # or: ./run_mario_face.sh
"""

import argparse
import sys

import cv2
import numpy as np

from .camera import Camera
from .mario_face_game import MarioFaceGameEngine, RESOLUTION, WINDOW_NAME
from .face_landmarker import FaceLandmarkerDetector
from .face_crop import FaceCropper
from .pose_detector import PoseDetector
from .sound_manager import SoundManager
from .utils import rgb_to_mp_image

MODEL_PATH = "models/pose_landmarker_lite.task"
FACE_MODEL_PATH = "models/face_landmarker.task"


def main() -> int:
    parser = argparse.ArgumentParser(description="Juego Camara — Mario Face Jump Game")
    parser.add_argument(
        "-c", "--camera",
        type=int,
        default=0,
        help="Camera device index (0=/dev/video0, 1=/dev/video1, ...)",
    )
    args = parser.parse_args()

    width, height = RESOLUTION

    try:
        camera = Camera(source=args.camera, width=width, height=height)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        detector = PoseDetector(
            model_path=MODEL_PATH,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Run ./run_mario_face.sh to download the model automatically.", file=sys.stderr)
        camera.release()
        return 1

    try:
        face_landmarker = FaceLandmarkerDetector(
            model_path=FACE_MODEL_PATH,
            num_faces=1,
            min_face_detection_confidence=0.3,
            min_face_presence_confidence=0.3,
            min_tracking_confidence=0.3,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Run ./run_mario_face.sh to download the model automatically.", file=sys.stderr)
        camera.release()
        return 1

    face_cropper = FaceCropper()

    engine = MarioFaceGameEngine(width, height, SoundManager(), face_landmarker, face_cropper)
    connections = list(detector.connections)

    print(f"Juego Camara — Mario Face Jump Game (camera /dev/video{args.camera})")
    print("Your real face replaces Mario's head! Physically jump to make Mario jump and clear obstacles!")
    print("Controls: SPACE = start/restart | q = quit")

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    display = np.zeros((height, width, 3), dtype=np.uint8)

    try:
        while True:
            ret, frame = camera.read_frame()
            if not ret:
                print("Warning: failed to read frame from camera.", file=sys.stderr)
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = rgb_to_mp_image(rgb)
            results = detector.detect(mp_image)

            if len(results) > 0 and results[0].success:
                points = results[0].landmark_points(width, height, 0.5)
            else:
                points = []

            engine.detect_face(rgb, frame)
            engine.update(points, connections)
            engine.render(display, connections)

            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break

            engine.handle_key(key)

    finally:
        face_landmarker.close()
        camera.release()
        detector.close()
        engine.close()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
