"""
Auto-reframing engine using MediaPipe face detection.
Converts landscape video to 9:16 vertical with smooth face tracking.
"""

import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from loguru import logger


class AutoReframer:
    """
    Face-tracking auto-reframer for 9:16 vertical crop.
    Uses moving-average smoothing to eliminate jitter.
    """

    def __init__(self, smoothing_window: int = 15, aspect_ratio: float = 9 / 16):
        self.aspect_ratio = aspect_ratio
        self.smoothing_window = smoothing_window
        self._center_history = deque(maxlen=smoothing_window)
        self._face_detection = None

    def _init_detector(self):
        """Lazy-init MediaPipe to avoid resource leaks on import."""
        if self._face_detection is None:
            mp_face = mp.solutions.face_detection
            self._face_detection = mp_face.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.5,
            )
        return self._face_detection

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process a single frame: detect face, compute smoothed crop.

        Args:
            frame: BGR image (h, w, 3)

        Returns:
            Cropped frame in 9:16 aspect ratio.
        """
        detector = self._init_detector()
        h, w, _ = frame.shape
        target_w = int(h * self.aspect_ratio)

        # Ensure target doesn't exceed frame width
        if target_w >= w:
            return frame

        # Detect face
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

        center_x = w // 2  # Default: center of frame

        if results.detections:
            # Use the largest face (by bounding box area)
            best_detection = max(
                results.detections,
                key=lambda d: d.location_data.relative_bounding_box.width
                              * d.location_data.relative_bounding_box.height,
            )
            bbox = best_detection.location_data.relative_bounding_box
            face_cx = int((bbox.xmin + bbox.width / 2) * w)
            center_x = face_cx

        # Smoothing: moving average over recent center positions
        self._center_history.append(center_x)
        smoothed_center = int(np.mean(self._center_history))

        # Clamp to frame bounds
        left = max(0, min(w - target_w, smoothed_center - target_w // 2))
        right = left + target_w

        return frame[:, left:right]

    def reset(self):
        """Clear smoothing history (call between different videos)."""
        self._center_history.clear()

    def close(self):
        """Release MediaPipe resources."""
        if self._face_detection is not None:
            self._face_detection.close()
            self._face_detection = None
        self._center_history.clear()
        logger.debug("AutoReframer resources released")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()


# Factory function instead of module-level singleton (prevents memory leaks)
def create_reframer(**kwargs) -> AutoReframer:
    """Create a new AutoReframer instance. Use as context manager."""
    return AutoReframer(**kwargs)
