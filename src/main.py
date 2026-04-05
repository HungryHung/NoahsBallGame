import time

import cv2

from ball import Ball
from body_tracker import BodyTracker
from interactions import InteractionHandler
from overlays import OverlayRenderer
from pose_estimator import PoseEstimator
import sounds

# MediaPipe pose connections (pairs of landmark indices)
_POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27),
    (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), (15, 17),
    (15, 19), (15, 21), (16, 18), (16, 20), (16, 22), (17, 19),
    (18, 20),
]


def draw_skeleton(frame, result):
    """Draw pose skeleton on the frame."""
    if result is None:
        return
    h, w = frame.shape[:2]
    for landmarks in result.pose_landmarks:
        points = []
        for lm in landmarks:
            px, py = int(lm.x * w), int(lm.y * h)
            points.append((px, py))
        for i, j in _POSE_CONNECTIONS:
            if i < len(points) and j < len(points):
                cv2.line(frame, points[i], points[j], (0, 255, 0), 2)
        for pt in points:
            cv2.circle(frame, pt, 4, (0, 0, 255), -1)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    estimator = PoseEstimator()
    tracker = BodyTracker()

    # Get frame dimensions for ball spawn
    ret, init_frame = cap.read()
    if not ret:
        print("Error: Could not read initial frame.")
        return
    frame_h, frame_w = init_frame.shape[:2]
    ball = Ball(frame_w // 2, frame_h // 4)
    interaction = InteractionHandler()
    overlay = OverlayRenderer()

    show_skeleton = True
    prev_time = time.time()

    cv2.namedWindow("NoahsBallGame", cv2.WINDOW_NORMAL)
    print("NoahsBallGame started. Press 'q' to quit, 's' to toggle skeleton, 'r' to reset ball.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame_h, frame_w = frame.shape[:2]

        # Timing
        now = time.time()
        dt = now - prev_time
        prev_time = now

        # Pose estimation
        result = estimator.estimate(frame)

        # Body tracking
        tracker.update(result, frame_w, frame_h, dt)

        # Interactions (grab, throw, punch, headbutt)
        hit = interaction.update(ball, tracker)
        if hit in ("punch", "headbutt", "throw"):
            ball.flash(hit)
            sounds.play(hit)
        elif hit == "grab":
            sounds.play("grab")

        # Ball physics
        ball.update(dt, frame_w, frame_h)

        # Draw ball
        ball.draw(frame)

        # Draw overlays (gloves + helmet)
        overlay.draw(frame, tracker)

        # Draw skeleton
        if show_skeleton:
            draw_skeleton(frame, result)

        # FPS counter
        fps = 1.0 / dt if dt > 0 else 0
        cv2.putText(frame, f"{fps:.0f} FPS", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("NoahsBallGame", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            show_skeleton = not show_skeleton
        elif key == ord("r"):
            ball.reset(frame_w // 2, frame_h // 4)

    estimator.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
