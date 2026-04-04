import cv2
import mediapipe as mp
from mediapipe import solutions as mp_solutions

from pose_estimator import PoseEstimator


def draw_skeleton(frame, result):
    """Draw pose skeleton on the frame."""
    if result is None:
        return
    for landmarks in result.pose_landmarks:
        mp_solutions.drawing_utils.draw_landmarks(
            frame,
            landmarks,
            mp_solutions.pose.POSE_CONNECTIONS,
            mp_solutions.drawing_styles.get_default_pose_landmarks_style(),
        )


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    estimator = PoseEstimator()
    show_skeleton = True

    cv2.namedWindow("NoahsBallGame", cv2.WINDOW_NORMAL)
    print("NoahsBallGame started. Press 'q' to quit, 's' to toggle skeleton.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        result = estimator.estimate(frame)

        if show_skeleton:
            draw_skeleton(frame, result)

        cv2.imshow("NoahsBallGame", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            show_skeleton = not show_skeleton

    estimator.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
