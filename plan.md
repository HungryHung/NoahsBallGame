# Plan: Noah's Ball Game

## Summary
Create a new repo (`NoahsBallGame`) for an interactive AR ball game where a player uses their hands (with Mickey Mouse glove overlays) and head (with bicycle helmet overlay) to grab, throw, punch, and headbutt a virtual soccer ball on screen. The ball is a classic black-and-white football (truncated icosahedron pattern: black pentagons + white hexagons). The ball follows physics (gravity, bouncing off frame edges) and can settle on the ground. Built on the same tech stack as MovementCoach (MediaPipe + OpenCV), reusing the pose estimation foundation.

## Phase 1: Project Setup & Pose Foundation
1. Create new repo folder `c:\Repos\NoahsBallGame` with standard Python project structure, then **switch workspace** to it
2. Initialize local git repo (`git init`), create `.gitignore` (Python template: `__pycache__/`, `.venv/`, `*.pyc`, etc.)
3. Install GitHub CLI if not present (`winget install --id GitHub.cli`), then authenticate (`gh auth login`)
4. Create **public** remote repo on GitHub (`gh repo create NoahsBallGame --public --source=. --remote=origin`)
5. Copy and adapt `PoseEstimator` from MovementCoach (`c:\Repos\MovementCoach\src\pose_estimator.py`) — keep MediaPipe PoseLandmarker setup, landmark extraction, and the `pose_landmarker_lite.task` model file
6. Copy and adapt camera loop from MovementCoach `main.py` — webcam capture, frame mirroring, display loop, quit on `q`
7. Create `requirements.txt` (mediapipe, opencv-python, numpy)
8. Initial commit and push to remote
9. **Verify**: Skeleton renders on webcam feed, hand (wrist landmarks 15/16) and head (nose landmark 0) positions are accessible

## Phase 2: Ball Physics Engine
1. Create `ball.py` with a `Ball` class:
   - Properties: `pos` (x, y in pixels), `vel` (vx, vy), `radius`, `gravity`, `restitution` (energy loss on bounce, e.g. 0.7), `friction` (for ground sliding)
   - `update(dt)`: Apply gravity to vy, update position, handle wall/floor/ceiling collisions
   - Wall collisions: Bounce off all 4 frame edges (reverse velocity component, multiply by restitution)
   - Floor settling: When velocity is very small and ball is on floor, set velocity to zero (ball rests)
   - `draw(frame)`: Render as a classic soccer ball — white circle base with black pentagon pattern drawn using OpenCV. The pattern rotates subtly based on ball velocity to give a spin illusion
2. Ball spawns at center of screen initially, falls to floor
3. **Verify**: Ball drops, bounces off floor with decreasing height, settles. Bounces off side walls and ceiling.

## Phase 3: Hand & Head Tracking
1. Create `body_tracker.py`:
   - Extract hand positions: left wrist (landmark 15), right wrist (landmark 16) — convert from normalized (0-1) to pixel coordinates
   - Extract head position: nose (landmark 0) — convert to pixel coords
   - Track velocity of hands and head: store previous frame positions, compute per-frame velocity vectors
   - Expose: `left_hand_pos`, `right_hand_pos`, `head_pos`, `left_hand_vel`, `right_hand_vel`, `head_vel`
2. **Verify**: Print/visualize hand and head positions + velocity vectors on screen

## Phase 4: Collision Detection & Interaction
1. Create `interactions.py` with collision and gesture logic:
   - **Grab detection**: Both hands within grab_radius of ball AND ball is settled or slow → ball state = "held"
   - **Held state**: Ball position follows midpoint of both hands (ball moves with hands)
   - **Throw detection**: While held, if hands move upward with velocity > threshold AND hands separate (release) → ball state = "free", ball gets velocity from hand movement (scaled for fun factor)
   - **Punch detection**: Single hand moving fast (velocity > punch_threshold) AND hand collides with ball → apply impulse to ball in direction of hand velocity
   - **Headbutt detection**: Head collides with ball AND head has downward/forward velocity → apply impulse to ball
   - Collision = distance between body part center and ball center < sum of radii
2. Tuning constants (adjustable): `GRAB_RADIUS`, `THROW_VELOCITY_THRESHOLD`, `PUNCH_VELOCITY_THRESHOLD`, `IMPULSE_SCALE`, `GRAVITY`
3. **Verify**: Can grab ball with both hands, throw it up, punch it, headbutt it. Ball responds naturally.

## Phase 5: PNG Overlays (Mickey Mouse Gloves & Helmet)
1. Create `assets/` folder with PNG images:
   - `glove_left.png` — Mickey Mouse glove, transparent background (~200x200px)
   - `glove_right.png` — Mirrored version
   - `helmet.png` — Bicycle helmet, transparent background (~200x200px)
   - Player provides or we source/create these assets (could use simple hand-drawn PNGs or free assets)
2. Create `overlays.py`:
   - `overlay_png(frame, image, position, scale)`: Alpha-blend a transparent PNG onto the frame at a given position and scale
   - Scale gloves relative to the distance between wrist and elbow (approximates hand size)
   - Scale helmet relative to distance between ears (landmarks 7, 8) or a fixed ratio of shoulder width
   - Position gloves centered on wrist landmarks
   - Position helmet centered above nose landmark (offset upward to sit on top of head)
   - Handle edge cases: landmarks near frame edge (clip overlay to frame bounds)
3. **Verify**: Gloves track hands smoothly, helmet sits on head correctly. Overlays scale with distance from camera.

## Phase 6: Integration & Polish
1. Wire everything together in `main.py` game loop:
   ```
   while True:
     1. Capture frame, mirror
     2. Pose estimation → landmarks
     3. Update body_tracker (positions + velocities)
     4. Process interactions (grab/throw/punch/headbutt)
     5. Update ball physics
     6. Draw ball on frame
     7. Draw glove overlays on frame
     8. Draw helmet overlay on frame
     9. Optionally draw skeleton (toggle with key)
     10. Display frame
   ```
2. Add keyboard controls:
   - `q` — Quit
   - `r` — Reset ball to center
   - `s` — Toggle skeleton visibility
3. Tune physics constants for fun factor (gravity, bounce, impulse scaling)
4. Add visual feedback: ball changes color briefly on hit, small particle effect or flash
5. **Verify**: Full game loop runs smoothly at 20+ FPS. All interactions work. Overlays render correctly.

## Project Structure
```
NoahsBallGame/
├── README.md
├── plan.md
├── requirements.txt
├── assets/
│   ├── glove_left.png
│   ├── glove_right.png
│   └── helmet.png
├── models/
│   └── pose_landmarker_lite.task
└── src/
    ├── main.py              — Game loop, window management
    ├── pose_estimator.py    — MediaPipe pose detection (adapted from MovementCoach)
    ├── ball.py              — Ball physics + soccer ball rendering (pentagon pattern)
    ├── body_tracker.py      — Hand/head position & velocity tracking
    ├── interactions.py      — Grab, throw, punch, headbutt logic
    └── overlays.py          — PNG overlay rendering (gloves, helmet)
```

## Decisions
- **New repo**: `NoahsBallGame` — game is a fundamentally different application from MovementCoach
- **Soccer ball**: Classic black-and-white football with pentagon/hexagon pattern (truncated icosahedron), drawn with OpenCV
- **Free play only**: No scoring, just sandbox interaction
- **PNG overlays**: More realistic Mickey Mouse gloves and bicycle helmet using transparent PNGs
- **Ball settles**: Ball can come to rest on the ground; player picks it up with both hands
- **2D physics**: Ball physics in pixel space (no 3D depth for simplicity)
- **Wrist landmarks for hands**: Using wrist positions (landmarks 15/16) as hand centers — sufficient for collision detection without needing separate MediaPipe Hand model

## Further Considerations
- **Asset sourcing**: Need to find or create the Mickey Mouse glove and bicycle helmet PNG images with transparent backgrounds. Could use simple hand-drawn PNGs, AI-generated images, or free game assets. Keep them simple — a 2-year-old won't notice imperfections.
- **Performance**: PNG alpha blending can be slow if images are large. Pre-scale assets to reasonable sizes. Target 20+ FPS.
- **Hand landmark precision**: Wrist landmarks (15/16) are good enough for collision. If grab detection needs more precision (e.g., detecting open vs closed hand), could add MediaPipe HandLandmarker as a future enhancement, but this adds complexity and latency.
