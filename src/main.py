"""Main entry point: webcam pose detection with mimicking silhouette characters.

Pipeline:
    camera.read_frame → BGR→RGB conversion → mp.Image → PoseLandmarker.detect →
    CharacterManager.update → CharacterManager.render → display with OpenCV
"""

import argparse
import sys

import cv2

from .camera import Camera
from .character import CharacterManager
from .pose_detector import PoseDetector
from .utils import rgb_to_mp_image

WINDOW_NAME = "Juego Camara"
RESOLUTION = (640, 480)
MODEL_PATH = "models/pose_landmarker_heavy.task"


def main() -> int:
    parser = argparse.ArgumentParser(description="Juego Camara — pose silhouette characters")
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
            num_poses=4,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=True,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Run ./run.sh to download the model automatically.", file=sys.stderr)
        camera.release()
        return 1

    manager = CharacterManager(width, height, max_persons=4, smooth_alpha=0.3)
    connections = list(detector.connections)

    print(f"Juego Camara — pose silhouette character(s) (camera /dev/video{args.camera})")
    print(f"Multi-person mode (max {manager._max_persons} people)")
    print("Controls: 'q' = quit | 'm' = toggle mirror | 's' = cycle style")

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    try:
        while True:
            ret, frame = camera.read_frame()
            if not ret:
                print("Warning: failed to read frame from camera.", file=sys.stderr)
                break

            # MediaPipe Tasks requires RGB in mp.Image format
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = rgb_to_mp_image(rgb)

            results = detector.detect(mp_image)
            manager.update(results, connections)
            manager.render(frame)

            # On-screen status
            mirror_label = " MIRROR" if manager._mirror_mode else ""
            style_label = f" style: {manager.style_name}"
            people_label = f" people: {manager.num_people}" if manager.num_people > 1 else ""
            cv2.putText(
                frame,
                f"Pose: {manager.num_people} person(s){mirror_label}{people_label}{style_label}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # q or Esc
                break
            elif key == ord("m"):
                on = manager.toggle_mirror()
                print(f"Mirror mode: {'ON' if on else 'OFF'}")
            elif key == ord("s"):
                idx = manager.cycle_style()
                print(f"Style: {manager.style_name}")
    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
