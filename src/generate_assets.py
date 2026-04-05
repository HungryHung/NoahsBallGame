"""Generate placeholder PNG assets for gloves and helmet.

Run once: python generate_assets.py
Creates assets/glove_left.png, assets/glove_right.png, assets/helmet.png
"""

import os

import cv2
import numpy as np

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _make_glove(size=200, flip=False):
    """Create a simple Mickey Mouse-style glove (white with black outline)."""
    img = np.zeros((size, size, 4), dtype=np.uint8)  # BGRA, transparent

    cx, cy = size // 2, size // 2 + 10
    # Palm (white circle)
    cv2.circle(img, (cx, cy), size // 3, (255, 255, 255, 255), -1)
    cv2.circle(img, (cx, cy), size // 3, (0, 0, 0, 255), 3)

    # Thumb
    tx = cx - size // 3 if not flip else cx + size // 3
    cv2.circle(img, (tx, cy - 5), size // 7, (255, 255, 255, 255), -1)
    cv2.circle(img, (tx, cy - 5), size // 7, (0, 0, 0, 255), 3)

    # Three fingers (rounded bumps on top)
    for i, offset in enumerate([-1, 0, 1]):
        fx = cx + offset * (size // 6)
        fy = cy - size // 3 - size // 10
        cv2.ellipse(img, (fx, fy), (size // 8, size // 5), 0, 0, 360,
                    (255, 255, 255, 255), -1)
        cv2.ellipse(img, (fx, fy), (size // 8, size // 5), 0, 0, 360,
                    (0, 0, 0, 255), 3)

    # Wrist cuff (light blue band at bottom)
    cuff_y = cy + size // 3
    cv2.ellipse(img, (cx, cuff_y), (size // 3, size // 8), 0, 0, 180,
                (230, 200, 150, 255), -1)
    cv2.ellipse(img, (cx, cuff_y), (size // 3, size // 8), 0, 0, 180,
                (0, 0, 0, 255), 2)

    if flip:
        img = cv2.flip(img, 1)

    return img


def _make_helmet(size=200):
    """Create a simple bicycle helmet shape (blue dome)."""
    img = np.zeros((size, size, 4), dtype=np.uint8)

    cx, cy = size // 2, size // 2 + 10

    # Main dome (blue)
    cv2.ellipse(img, (cx, cy), (size // 2 - 10, size // 3), 0, 180, 360,
                (200, 120, 30, 255), -1)  # blue in BGR
    cv2.ellipse(img, (cx, cy), (size // 2 - 10, size // 3), 0, 180, 360,
                (0, 0, 0, 255), 3)

    # Visor / brim at bottom
    visor_y = cy + 5
    cv2.ellipse(img, (cx, visor_y), (size // 2 - 5, size // 10), 0, 0, 180,
                (150, 90, 20, 255), -1)
    cv2.ellipse(img, (cx, visor_y), (size // 2 - 5, size // 10), 0, 0, 180,
                (0, 0, 0, 255), 2)

    # Vent lines on top
    for i in range(-2, 3):
        x = cx + i * (size // 8)
        y1 = cy - size // 4
        y2 = cy - size // 8
        cv2.line(img, (x, y1), (x, y2), (0, 0, 0, 180), 2)

    return img


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    glove_left = _make_glove(200, flip=False)
    glove_right = _make_glove(200, flip=True)
    helmet = _make_helmet(200)

    cv2.imwrite(os.path.join(ASSETS_DIR, "glove_left.png"), glove_left)
    cv2.imwrite(os.path.join(ASSETS_DIR, "glove_right.png"), glove_right)
    cv2.imwrite(os.path.join(ASSETS_DIR, "helmet.png"), helmet)

    print(f"Assets created in {ASSETS_DIR}:")
    print("  glove_left.png")
    print("  glove_right.png")
    print("  helmet.png")


if __name__ == "__main__":
    main()
