import numpy as np

# Tuning constants
GRAB_RADIUS = 100         # px – how close both hands must be to grab
GRAB_BALL_SPEED_MAX = 350 # px/s – ball can be grabbed if moving slower than this
THROW_VEL_THRESHOLD = 250  # px/s – minimum hand speed to count as a throw
PUNCH_VEL_THRESHOLD = 500  # px/s – minimum hand speed to count as a punch
HEADBUTT_VEL_THRESHOLD = 250  # px/s – minimum head speed for headbutt
IMPULSE_SCALE = 1.2        # multiplier on hand/head velocity → ball velocity
RELEASE_DISTANCE = 140     # px – hands must separate this far to release a grab


class InteractionHandler:
    def __init__(self):
        self.state = "free"  # "free" or "held"

    def update(self, ball, tracker):
        """Process grab / throw / punch / headbutt interactions.

        Returns the hit type string ('grab', 'throw', 'punch', 'headbutt')
        or None if no interaction occurred this frame.
        """
        if self.state == "held":
            return self._update_held(ball, tracker)
        else:
            # Check grab FIRST — if both hands are near the ball, grab wins over punch
            if self._check_grab(ball, tracker):
                return "grab"
            hit = self._check_punch(ball, tracker)
            if hit:
                return hit
            hit = self._check_headbutt(ball, tracker)
            if hit:
                return hit
        return None

    # ------------------------------------------------------------------
    # Held state
    # ------------------------------------------------------------------
    def _update_held(self, ball, tracker):
        lh = tracker.left_hand_pos
        rh = tracker.right_hand_pos
        if lh is None or rh is None:
            # Lost tracking → release
            self.state = "free"
            return None

        midpoint = (lh + rh) / 2
        hand_dist = np.linalg.norm(lh - rh)

        # Release when hands separate
        if hand_dist > RELEASE_DISTANCE:
            self.state = "free"
            # Throw velocity = average hand velocity, scaled
            avg_vel = (tracker.left_hand_vel + tracker.right_hand_vel) / 2
            ball.vel = avg_vel * IMPULSE_SCALE
            return "throw"

        # Otherwise ball follows hand midpoint
        ball.pos = midpoint.copy()
        ball.vel[:] = 0.0
        return None

    # ------------------------------------------------------------------
    # Grab detection (both hands near a slow/settled ball)
    # ------------------------------------------------------------------
    def _check_grab(self, ball, tracker):
        lh = tracker.left_hand_pos
        rh = tracker.right_hand_pos
        if lh is None or rh is None:
            return False

        ball_speed = np.linalg.norm(ball.vel)
        if ball_speed > GRAB_BALL_SPEED_MAX:
            return False

        ld = np.linalg.norm(lh - ball.pos)
        rd = np.linalg.norm(rh - ball.pos)
        if ld < GRAB_RADIUS and rd < GRAB_RADIUS:
            self.state = "held"
            ball.vel[:] = 0.0
            return True
        return False

    # ------------------------------------------------------------------
    # Punch (single fast hand collides with ball)
    # ------------------------------------------------------------------
    def _check_punch(self, ball, tracker):
        for hand_pos, hand_vel in [
            (tracker.left_hand_pos, tracker.left_hand_vel),
            (tracker.right_hand_pos, tracker.right_hand_vel),
        ]:
            if hand_pos is None:
                continue
            dist = np.linalg.norm(hand_pos - ball.pos)
            speed = np.linalg.norm(hand_vel)
            if dist < ball.radius + 25 and speed > PUNCH_VEL_THRESHOLD:
                # Apply impulse in direction of hand velocity
                ball.vel = hand_vel * IMPULSE_SCALE
                return "punch"
        return None

    # ------------------------------------------------------------------
    # Headbutt (head moving UPWARD collides with ball)
    # ------------------------------------------------------------------
    def _check_headbutt(self, ball, tracker):
        if tracker.head_top_pos is None:
            return
        # Only trigger when head is moving upward (negative Y = upward in pixel coords)
        if tracker.head_vel[1] >= 0:
            return
        # Ball must be above the head top (not passing in front of face)
        if ball.pos[1] > tracker.head_top_pos[1]:
            return
        dist = np.linalg.norm(tracker.head_top_pos - ball.pos)
        speed = np.linalg.norm(tracker.head_vel)
        if dist < ball.radius + 35 and speed > HEADBUTT_VEL_THRESHOLD:
            ball.vel = tracker.head_vel * IMPULSE_SCALE
            return "headbutt"
        return None
