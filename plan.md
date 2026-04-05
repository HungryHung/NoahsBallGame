# Plan: Noah's Ball Game

## Summary
Create a new repo (`NoahsBallGame`) for an interactive AR ball game where a player uses their hands (with Mickey Mouse glove overlays) and head (with bicycle helmet overlay) to grab, throw, punch, and headbutt a virtual soccer ball on screen. The ball is a classic black-and-white football (truncated icosahedron pattern: black pentagons + white hexagons). The ball follows physics (gravity, bouncing off frame edges) and can settle on the ground. Built on the same tech stack as MovementCoach (MediaPipe + OpenCV), reusing the pose estimation foundation.

## Phase 1: Project Setup & Pose Foundation ✅
1. Create new repo folder `c:\Repos\NoahsBallGame` with standard Python project structure, then **switch workspace** to it
2. Initialize local git repo (`git init`), create `.gitignore` (Python template: `__pycache__/`, `.venv/`, `*.pyc`, etc.)
3. Install GitHub CLI if not present (`winget install --id GitHub.cli`), then authenticate (`gh auth login`)
4. Create **public** remote repo on GitHub (`gh repo create NoahsBallGame --public --source=. --remote=origin`)
5. Copy and adapt `PoseEstimator` from MovementCoach (`c:\Repos\MovementCoach\src\pose_estimator.py`) — keep MediaPipe PoseLandmarker setup, landmark extraction, and the `pose_landmarker_lite.task` model file
6. Copy and adapt camera loop from MovementCoach `main.py` — webcam capture, frame mirroring, display loop, quit on `q`
7. Create `requirements.txt` (mediapipe, opencv-python, numpy, sounddevice)
8. Initial commit and push to remote
9. **Verify**: Skeleton renders on webcam feed, hand (wrist landmarks 15/16) and head (nose landmark 0) positions are accessible

**Note**: The `mediapipe.solutions` API is not available on Python 3.14. Skeleton drawing uses a custom implementation with raw landmark coordinates and OpenCV instead of `mp.solutions.drawing_utils`.

## Phase 2: Ball Physics Engine ✅
1. Create `ball.py` with a `Ball` class:
   - Properties: `pos` (x, y in pixels), `vel` (vx, vy), `radius`, `gravity` (400), `restitution` (0.65), `friction` (0.98)
   - `update(dt)`: Apply gravity to vy, update position, handle wall/floor/ceiling collisions
   - Wall collisions: Bounce off all 4 frame edges (reverse velocity component, multiply by restitution)
   - Floor settling: When velocity is very small and ball is on floor, set velocity to zero (ball rests)
   - `draw(frame)`: Render as a classic soccer ball using real truncated icosahedron geometry — 12 black pentagons + 20 white hexagons with seam lines, 3D-rotated and projected based on velocity-driven spin. Painter's algorithm for correct face layering.
   - `flash(hit_type)`: Briefly tints ball on hit — orange for punch, yellow for headbutt, blue for throw
2. Ball spawns at top-center of screen initially, falls to floor
3. **Verify**: Ball drops, bounces off floor with decreasing height, settles. Bounces off side walls and ceiling.

## Phase 3: Hand & Head Tracking ✅
1. Create `body_tracker.py`:
   - Extract hand positions: left wrist (landmark 15), right wrist (landmark 16) — convert from normalized (0-1) to pixel coordinates
   - Extract head position: nose (landmark 0) — convert to pixel coords
   - Extract head top position: estimated by projecting 2.5× nose-to-eye distance above the nose — used for headbutt collision and helmet placement
   - Extract elbow positions (landmarks 13, 14) and shoulder width (landmarks 11, 12) — used for overlay scaling
   - Track velocity of hands and head: store previous frame positions, compute per-frame velocity vectors
   - Expose: `left_hand_pos`, `right_hand_pos`, `head_pos`, `head_top_pos`, `left_hand_vel`, `right_hand_vel`, `head_vel`, `left_elbow_pos`, `right_elbow_pos`, `shoulder_width`
2. **Verify**: Print/visualize hand and head positions + velocity vectors on screen

## Phase 4: Collision Detection & Interaction ✅
1. Create `interactions.py` with collision and gesture logic:
   - **Grab detection**: Both hands within `GRAB_RADIUS` (100px) of ball AND ball speed < `GRAB_BALL_SPEED_MAX` (350 px/s) → ball state = "held". Grab is checked before punch to prevent accidental punches.
   - **Held state**: Ball position follows midpoint of both hands (ball moves with hands)
   - **Throw detection**: While held, if hands separate beyond `RELEASE_DISTANCE` (140px) → ball state = "free", ball gets average hand velocity × `IMPULSE_SCALE` (1.2)
   - **Punch detection**: Single hand moving fast (velocity > `PUNCH_VEL_THRESHOLD` 500 px/s) AND hand collides with ball → apply impulse to ball in direction of hand velocity
   - **Headbutt detection**: Head top collides with ball AND head is moving **upward** (negative Y velocity) AND ball is above head → apply impulse. Prevents accidental headbutts when ball passes in front of face.
   - Collision = distance between body part center and ball center < sum of radii
   - Returns hit type string (`'grab'`, `'throw'`, `'punch'`, `'headbutt'`) or `None` for visual/audio feedback
2. Tuning constants (adjustable): `GRAB_RADIUS`, `GRAB_BALL_SPEED_MAX`, `THROW_VEL_THRESHOLD`, `PUNCH_VEL_THRESHOLD`, `HEADBUTT_VEL_THRESHOLD`, `IMPULSE_SCALE`, `RELEASE_DISTANCE`
3. **Verify**: Can grab ball with both hands, throw it up, punch it, headbutt it. Ball responds naturally.

## Phase 5: PNG Overlays (Mickey Mouse Gloves & Helmet) ✅
1. Placeholder assets generated via `generate_assets.py`:
   - `glove_left.png` — Mickey Mouse glove, transparent background (200x200px)
   - `glove_right.png` — Mirrored version
   - `helmet.png` — Bicycle helmet, transparent background (200x200px)
   - Can be replaced with real PNG assets at any time
2. Create `overlays.py` with `OverlayRenderer`:
   - Alpha-blend transparent PNGs onto the frame at body part positions
   - Scale gloves relative to the distance between wrist and elbow
   - Scale helmet relative to shoulder width
   - Position gloves centered on wrist landmarks
   - Position helmet centered on `head_top_pos` (top of head)
   - Handle edge cases: landmarks near frame edge (clip overlay to frame bounds)
3. **Verify**: Gloves track hands smoothly, helmet sits on head correctly. Overlays scale with distance from camera.

## Phase 6: Integration & Polish ✅
1. Full game loop in `main.py`:
   ```
   while True:
     1. Capture frame, mirror
     2. Pose estimation → landmarks
     3. Update body_tracker (positions + velocities)
     4. Process interactions (grab/throw/punch/headbutt)
     5. Trigger ball flash + sound on hit
     6. Update ball physics
     7. Draw ball on frame
     8. Draw glove + helmet overlays on frame
     9. Optionally draw skeleton (toggle with key)
     10. Show FPS counter
     11. Display frame
   ```
2. Keyboard controls:
   - `q` — Quit
   - `r` — Reset ball to center
   - `s` — Toggle skeleton visibility
3. Tuned physics constants for fun factor (gravity=400, restitution=0.65, impulse_scale=1.2)
4. Visual feedback: ball flashes color on hit (orange=punch, yellow=headbutt, blue=throw)
5. Sound effects via `sounddevice` with persistent low-latency audio stream:
   - Punch: bouncy "boing" spring sound (`boing.wav`)
   - Headbutt: cartoon "bonk" thud (`bonk.wav`)
   - Throw: quick "whoosh" (`whoosh.wav`)
   - Grab: soft "pop" (`pop.wav`)
   - Sounds synthesized via `generate_sounds.py`, preloaded into memory, played via callback-based `OutputStream` for near-zero latency
6. FPS counter displayed in top-left corner
7. **Verify**: Full game loop runs smoothly at 20+ FPS. All interactions work. Overlays render correctly.

## Project Structure
```
NoahsBallGame/
├── .gitignore
├── plan.md
├── requirements.txt
├── assets/
│   ├── glove_left.png       — Mickey Mouse glove overlay (left hand)
│   ├── glove_right.png      — Mickey Mouse glove overlay (right hand)
│   ├── helmet.png           — Bicycle helmet overlay
│   ├── boing.wav            — Punch sound effect
│   ├── bonk.wav             — Headbutt sound effect
│   ├── whoosh.wav           — Throw sound effect
│   └── pop.wav              — Grab sound effect
├── models/
│   └── pose_landmarker_lite.task
└── src/
    ├── main.py              — Game loop, window management, FPS display
    ├── pose_estimator.py    — MediaPipe pose detection (tasks API)
    ├── ball.py              — Ball physics + truncated icosahedron rendering + hit flash
    ├── body_tracker.py      — Hand/head/elbow position & velocity tracking
    ├── interactions.py      — Grab, throw, punch, headbutt logic
    ├── overlays.py          — PNG overlay rendering (gloves, helmet)
    ├── sounds.py            — Low-latency sound playback (sounddevice)
    ├── generate_assets.py   — Script to generate placeholder PNG assets
    └── generate_sounds.py   — Script to synthesize WAV sound effects
```

## Decisions
- **New repo**: `NoahsBallGame` — game is a fundamentally different application from MovementCoach
- **Soccer ball**: Classic black-and-white football with truncated icosahedron geometry (12 black pentagons + 20 white hexagons), 3D-rotated and projected in real-time via OpenCV
- **Free play only**: No scoring, just sandbox interaction
- **PNG overlays**: Mickey Mouse gloves and bicycle helmet using transparent PNGs (placeholder assets generated, swappable)
- **Ball settles**: Ball can come to rest on the ground; player picks it up with both hands
- **2D physics**: Ball physics in pixel space (no 3D depth for simplicity)
- **Wrist landmarks for hands**: Using wrist positions (landmarks 15/16) as hand centers — sufficient for collision detection without needing separate MediaPipe Hand model
- **Head top estimation**: Top of head projected from nose using eye landmarks — used for headbutt collision and helmet placement
- **Headbutt direction constraint**: Headbutt only triggers when head moves upward, preventing accidental hits from ball passing in front of face
- **Grab priority over punch**: Grab is checked before punch so approaching with both hands grabs rather than punches
- **Sound via sounddevice**: Using `sounddevice` with persistent `OutputStream` and callback for near-zero-latency audio. `winsound` was too slow. `pygame.mixer` doesn't support Python 3.14.
- **Custom skeleton drawing**: `mediapipe.solutions` not available on Python 3.14; skeleton drawn manually with OpenCV using known pose connection pairs

## Future Improvements
- **Better assets**: Replace placeholder glove/helmet PNGs with real images (AI-generated or free game assets)
- **Better sounds**: Replace synthesized WAVs with recorded sound files
- **Visual effects**: Particle bursts on impact, trail behind the ball
- **Multiple balls**: Spawn extra balls for more chaos
- **Score/counter**: Count headbutts or juggles
- **Hand landmark precision**: Could add MediaPipe HandLandmarker for open/closed hand detection, but adds complexity and latency
- **Performance**: PNG alpha blending can be optimized if needed. Currently targeting 20+ FPS.
