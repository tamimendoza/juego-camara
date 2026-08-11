"""Game entry point: webcam pose-controlled endless jumping game.

Pipeline:
    camera.read_frame → BGR→RGB conversion → mp.Image → PoseLandmarker.detect →
    GameEngine.update → GameEngine.render → display with OpenCV

The player jumps by physically raising above their standing baseline. A
miniatura character must clear scrolling obstacles. Speed increases every 5
obstacles passed. The player has 3 lives (hearts); losing all lives ends the game.

Usage:
    python3 -m src.game_main
    # or: ./run_game.sh
"""

import argparse
import sys

import cv2
import numpy as np

from .camera import Camera
from .game import GameEngine, RESOLUTION, WINDOW_NAME
from .pose_detector import PoseDetector
from .sound_manager import SoundManager
from .utils import rgb_to_mp_image

MODEL_PATH = "models/pose_landmarker_lite.task"


def main() -> int:
    parser = argparse.ArgumentParser(description="Juego Camara — Pose Jump Game")
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
        print("Run ./run_game.sh to download the model automatically.", file=sys.stderr)
        camera.release()
        return 1

    engine = GameEngine(width, height, sound_manager=SoundManager())
    connections = list(detector.connections)

    print(f"Juego Camara — Pose Jump Game (camera /dev/video{args.camera})")
    print("Physically jump to make the character jump. Avoid the obstacles!")
    print("Double jump: raise your shoulders a second time while airborne for extra height!")
    print("Controls: SPACE = start/restart | q = quit")

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1920, 1080)

    # Blank canvas for game rendering (no camera feed in game mode)
    display = np.zeros((height, width, 3), dtype=np.uint8)

    try:
        while True:
            ret, frame = camera.read_frame()
            if not ret:
                print("Warning: failed to read frame from camera.", file=sys.stderr)
                break

            # Detect pose (BGR → RGB → mp.Image)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = rgb_to_mp_image(rgb)
            results = detector.detect(mp_image)

            # Extract landmark pixel points for the first detected person
            if len(results) > 0 and results[0].success:
                points = results[0].landmark_points(width, height, 0.5)
            else:
                points = []

            engine.update(points, connections)
            engine.render(display, connections)

            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # q or Esc
                break

            engine.handle_key(key)

    finally:
        engine.close()
        camera.release()
        detector.close()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
