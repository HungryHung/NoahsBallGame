import numpy as np


# MediaPipe pose landmark indices
_LEFT_WRIST = 15
_RIGHT_WRIST = 16
_NOSE = 0
_LEFT_EYE = 2
_RIGHT_EYE = 5
_LEFT_ELBOW = 13
_RIGHT_ELBOW = 14
_LEFT_SHOULDER = 11
_RIGHT_SHOULDER = 12


class BodyTracker:
    def __init__(self):
        self.left_hand_pos = None   # (x, y) in pixels or None
        self.right_hand_pos = None
        self.head_pos = None
        self.head_top_pos = None  # top of head (for helmet / headbutt)
        self.left_elbow_pos = None
        self.right_elbow_pos = None
        self.shoulder_width = 0.0  # px distance between shoulders

        self.left_hand_vel = np.array([0.0, 0.0])
        self.right_hand_vel = np.array([0.0, 0.0])
        self.head_vel = np.array([0.0, 0.0])

        self._prev_left = None
        self._prev_right = None
        self._prev_head = None

    def update(self, result, frame_w, frame_h, dt):
        """Update tracked positions and velocities from pose landmarks.

        Args:
            result: PoseLandmarkerResult (or None if no person detected)
            frame_w: frame width in pixels
            frame_h: frame height in pixels
            dt: time delta in seconds since last frame
        """
        if result is None or not result.pose_landmarks:
            self.left_hand_pos = None
            self.right_hand_pos = None
            self.head_pos = None
            self.head_top_pos = None
            self.left_elbow_pos = None
            self.right_elbow_pos = None
            self.shoulder_width = 0.0
            self.left_hand_vel[:] = 0.0
            self.right_hand_vel[:] = 0.0
            self.head_vel[:] = 0.0
            self._prev_left = None
            self._prev_right = None
            self._prev_head = None
            return

        landmarks = result.pose_landmarks[0]

        # Extract and convert normalized coords to pixel coords
        lw = landmarks[_LEFT_WRIST]
        rw = landmarks[_RIGHT_WRIST]
        nose = landmarks[_NOSE]
        leye = landmarks[_LEFT_EYE]
        reye = landmarks[_RIGHT_EYE]
        le = landmarks[_LEFT_ELBOW]
        re = landmarks[_RIGHT_ELBOW]
        ls = landmarks[_LEFT_SHOULDER]
        rs = landmarks[_RIGHT_SHOULDER]

        self.left_hand_pos = np.array([lw.x * frame_w, lw.y * frame_h])
        self.right_hand_pos = np.array([rw.x * frame_w, rw.y * frame_h])
        self.head_pos = np.array([nose.x * frame_w, nose.y * frame_h])
        self.left_elbow_pos = np.array([le.x * frame_w, le.y * frame_h])
        self.right_elbow_pos = np.array([re.x * frame_w, re.y * frame_h])

        ls_px = np.array([ls.x * frame_w, ls.y * frame_h])
        rs_px = np.array([rs.x * frame_w, rs.y * frame_h])
        self.shoulder_width = np.linalg.norm(ls_px - rs_px)

        # Estimate top of head: project upward from nose by ~2.5× nose-to-eye distance
        mid_eye = np.array([
            (leye.x + reye.x) / 2 * frame_w,
            (leye.y + reye.y) / 2 * frame_h,
        ])
        nose_to_eye = np.linalg.norm(self.head_pos - mid_eye)
        self.head_top_pos = np.array([
            self.head_pos[0],
            self.head_pos[1] - nose_to_eye * 2.5,
        ])

        # Compute velocities from position delta
        if dt > 0:
            if self._prev_left is not None:
                self.left_hand_vel = (self.left_hand_pos - self._prev_left) / dt
            else:
                self.left_hand_vel = np.array([0.0, 0.0])

            if self._prev_right is not None:
                self.right_hand_vel = (self.right_hand_pos - self._prev_right) / dt
            else:
                self.right_hand_vel = np.array([0.0, 0.0])

            if self._prev_head is not None:
                self.head_vel = (self.head_pos - self._prev_head) / dt
            else:
                self.head_vel = np.array([0.0, 0.0])

        self._prev_left = self.left_hand_pos.copy()
        self._prev_right = self.right_hand_pos.copy()
        self._prev_head = self.head_pos.copy()
