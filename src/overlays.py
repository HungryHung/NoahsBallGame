import os

import cv2
import numpy as np

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _load_png(name):
    path = os.path.join(_ASSETS_DIR, name)
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)  # BGRA
    if img is None:
        raise FileNotFoundError(f"Asset not found: {path}")
    return img


class OverlayRenderer:
    def __init__(self):
        self._glove_left = _load_png("glove_left.png")
        self._glove_right = _load_png("glove_right.png")
        self._helmet = _load_png("helmet.png")

    def draw(self, frame, tracker):
        if tracker.left_hand_pos is not None and tracker.left_elbow_pos is not None:
            size = self._hand_size(tracker.left_hand_pos, tracker.left_elbow_pos)
            self._overlay(frame, self._glove_left, tracker.left_hand_pos, size)

        if tracker.right_hand_pos is not None and tracker.right_elbow_pos is not None:
            size = self._hand_size(tracker.right_hand_pos, tracker.right_elbow_pos)
            self._overlay(frame, self._glove_right, tracker.right_hand_pos, size)

        if tracker.head_top_pos is not None and tracker.shoulder_width > 0:
            size = int(tracker.shoulder_width * 0.7)
            size = max(size, 40)
            self._overlay(frame, self._helmet, tracker.head_top_pos, size)

    def _hand_size(self, wrist_pos, elbow_pos):
        dist = np.linalg.norm(wrist_pos - elbow_pos)
        size = int(dist * 0.8)
        return max(size, 30)

    def _overlay(self, frame, img, center, size):
        """Alpha-blend a BGRA image onto frame, centered at (cx, cy), scaled to size×size."""
        h, w = frame.shape[:2]
        if size < 5:
            return

        scaled = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)

        cx, cy = int(center[0]), int(center[1])
        x1 = cx - size // 2
        y1 = cy - size // 2
        x2 = x1 + size
        y2 = y1 + size

        # Clip to frame bounds
        sx1 = max(0, -x1)
        sy1 = max(0, -y1)
        sx2 = size - max(0, x2 - w)
        sy2 = size - max(0, y2 - h)

        dx1 = max(0, x1)
        dy1 = max(0, y1)
        dx2 = min(w, x2)
        dy2 = min(h, y2)

        if dx1 >= dx2 or dy1 >= dy2 or sx1 >= sx2 or sy1 >= sy2:
            return

        overlay_region = scaled[sy1:sy2, sx1:sx2]
        alpha = overlay_region[:, :, 3:4].astype(np.float32) / 255.0
        rgb = overlay_region[:, :, :3].astype(np.float32)

        roi = frame[dy1:dy2, dx1:dx2].astype(np.float32)
        blended = roi * (1 - alpha) + rgb * alpha
        frame[dy1:dy2, dx1:dx2] = blended.astype(np.uint8)
