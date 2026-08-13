"""Webcam capture module for Linux Ubuntu using OpenCV V4L2 backend."""

import cv2
import numpy as np


class Camera:
    """Wraps OpenCV VideoCapture for webcam video input on Linux."""

    def __init__(
        self,
        source: int = 0,
        width: int = 640,
        height: int = 480,
        backend: int = cv2.CAP_V4L2,
    ):
        """Open a webcam.

        Args:
            source: Camera device index (0 = /dev/video0).
            width: Target frame width in pixels.
            height: Target frame height in pixels.
            backend: OpenCV backend preference (CAP_V4L2 for Linux).
        """
        self._cap = cv2.VideoCapture(source, backend)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(source)
            if not self._cap.isOpened():
                raise RuntimeError(
                    "No webcam found at /dev/video0. "
                    "Ensure a camera is connected and not in use."
                )

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.width = width
        self.height = height

    def read_frame(self) -> tuple[bool, np.ndarray]:
        """Read a raw BGR frame from the webcam.

        Returns BGR (the native OpenCV format) so the frame can be drawn
        on directly. Callers that use MediaPipe should convert to RGB:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        Returns:
            (success, bgr_frame) — bgr_frame is None on failure.
        """
        ret, frame = self._cap.read()
        if not ret:
            return False, None
        return True, frame

    @property
    def frame_size(self) -> tuple[int, int]:
        """Return (width, height) of configured frames."""
        return self.width, self.height

    def is_opened(self) -> bool:
        return self._cap.isOpened()

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
