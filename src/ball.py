import math

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Truncated icosahedron geometry (precomputed at module load)
# ---------------------------------------------------------------------------

def _build_icosahedron():
    """Return 12 vertices and 30 edges of an icosahedron on the unit sphere."""
    phi = (1 + math.sqrt(5)) / 2
    raw = [
        (0, 1, phi), (0, -1, phi), (0, 1, -phi), (0, -1, -phi),
        (1, phi, 0), (-1, phi, 0), (1, -phi, 0), (-1, -phi, 0),
        (phi, 0, 1), (-phi, 0, 1), (phi, 0, -1), (-phi, 0, -1),
    ]
    verts = []
    for v in raw:
        a = np.array(v, dtype=float)
        verts.append(a / np.linalg.norm(a))

    # Find edges by shortest pairwise distance
    dists = []
    n = len(verts)
    for i in range(n):
        for j in range(i + 1, n):
            dists.append(np.linalg.norm(verts[i] - verts[j]))
    min_d = min(dists)
    threshold = min_d * 1.05

    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(verts[i] - verts[j]) < threshold:
                edges.append((i, j))

    return verts, edges


def _find_icosahedron_faces(verts, edges):
    """Find the 20 triangular faces of the icosahedron."""
    adj = {}
    for i, j in edges:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)
    faces = set()
    for i in adj:
        for j in adj[i]:
            for k in adj[j]:
                if k in adj[i] and k != i:
                    faces.add(tuple(sorted([i, j, k])))
    return list(faces)


def _order_polygon_verts(verts, indices, center):
    """Order vertex indices counter-clockwise around *center*."""
    center = center / np.linalg.norm(center)
    ref = np.array([1.0, 0, 0]) if abs(center[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(center, ref)
    u /= np.linalg.norm(u)
    v = np.cross(center, u)
    angles = []
    for idx in indices:
        d = verts[idx] - center
        angles.append(math.atan2(np.dot(d, v), np.dot(d, u)))
    return [idx for _, idx in sorted(zip(angles, indices))]


def _build_truncated_icosahedron():
    """Compute vertices, pentagon faces, hexagon faces, and all edges."""
    ico_v, ico_e = _build_icosahedron()
    ico_f = _find_icosahedron_faces(ico_v, ico_e)

    # Truncate each icosahedron edge at 1/3 and 2/3 → 60 new vertices
    trunc_verts = []
    edge_map = {}  # (i,j) → (near_i_idx, near_j_idx)
    for i, j in ico_e:
        v1 = (2 * ico_v[i] + ico_v[j]) / 3
        v2 = (ico_v[i] + 2 * ico_v[j]) / 3
        v1 /= np.linalg.norm(v1)
        v2 /= np.linalg.norm(v2)
        idx1 = len(trunc_verts); trunc_verts.append(v1)
        idx2 = len(trunc_verts); trunc_verts.append(v2)
        edge_map[(i, j)] = (idx1, idx2)
    trunc_verts = np.array(trunc_verts)  # (60, 3)

    # 12 pentagonal faces — one per icosahedron vertex
    pent_faces = []
    for vi in range(len(ico_v)):
        idxs = []
        for (a, b), (va, vb) in edge_map.items():
            if a == vi:
                idxs.append(va)
            elif b == vi:
                idxs.append(vb)
        pent_faces.append(_order_polygon_verts(trunc_verts, idxs, ico_v[vi]))

    # 20 hexagonal faces — one per icosahedron face
    hex_faces = []
    for a, b, c in ico_f:
        idxs = []
        for i, j in [(a, b), (b, c), (a, c)]:
            key = (min(i, j), max(i, j))
            va, vb = edge_map[key]
            idxs.extend([va, vb])
        center = (ico_v[a] + ico_v[b] + ico_v[c]) / 3
        hex_faces.append(_order_polygon_verts(trunc_verts, idxs, center))

    # Collect all unique edges from face boundaries
    all_edges = set()
    for face in pent_faces + hex_faces:
        n = len(face)
        for k in range(n):
            e = tuple(sorted((face[k], face[(k + 1) % n])))
            all_edges.add(e)

    return trunc_verts, pent_faces, hex_faces, list(all_edges)


_TV, _PF, _HF, _TE = _build_truncated_icosahedron()


# ---------------------------------------------------------------------------
# Ball class
# ---------------------------------------------------------------------------

class Ball:
    def __init__(self, x, y, radius=30, gravity=400, restitution=0.65, friction=0.98):
        self.pos = np.array([float(x), float(y)])
        self.vel = np.array([0.0, 0.0])
        self.radius = radius
        self.gravity = gravity
        self.restitution = restitution
        self.friction = friction
        self._spin_angle = 0.0
        self._flash_timer = 0.0  # seconds remaining for hit flash
        self._flash_color = None

    def reset(self, x, y):
        self.pos = np.array([float(x), float(y)])
        self.vel = np.array([0.0, 0.0])
        self._spin_angle = 0.0
        self._flash_timer = 0.0
        self._flash_color = None

    def update(self, dt, frame_w, frame_h):
        # Apply gravity
        self.vel[1] += self.gravity * dt

        # Update position
        self.pos += self.vel * dt

        # Spin based on horizontal velocity
        self._spin_angle += self.vel[0] * dt * 0.05

        # Wall collisions
        if self.pos[0] - self.radius < 0:
            self.pos[0] = self.radius
            self.vel[0] = -self.vel[0] * self.restitution
        if self.pos[0] + self.radius > frame_w:
            self.pos[0] = frame_w - self.radius
            self.vel[0] = -self.vel[0] * self.restitution
        if self.pos[1] - self.radius < 0:
            self.pos[1] = self.radius
            self.vel[1] = -self.vel[1] * self.restitution
        if self.pos[1] + self.radius > frame_h:
            self.pos[1] = frame_h - self.radius
            self.vel[1] = -self.vel[1] * self.restitution
            self.vel[0] *= self.friction

        # Settle on floor
        speed = np.linalg.norm(self.vel)
        if self.pos[1] + self.radius >= frame_h - 1 and speed < 15:
            self.vel[:] = 0.0
            self.pos[1] = frame_h - self.radius

        # Decay flash timer
        if self._flash_timer > 0:
            self._flash_timer -= dt

    def flash(self, hit_type):
        """Trigger a brief color flash on the ball."""
        self._flash_timer = 0.15
        if hit_type == "punch":
            self._flash_color = (0, 100, 255)   # orange
        elif hit_type == "headbutt":
            self._flash_color = (0, 255, 255)   # yellow
        elif hit_type == "throw":
            self._flash_color = (255, 150, 0)   # blue
        else:
            self._flash_color = (0, 255, 0)     # green

    def draw(self, frame):
        cx, cy = int(self.pos[0]), int(self.pos[1])
        r = self.radius

        # Rotation matrix (spin around Y + gentle wobble around X)
        ay = self._spin_angle
        ax = self._spin_angle * 0.3
        cy_, sy = math.cos(ay), math.sin(ay)
        cx_, sx = math.cos(ax), math.sin(ax)
        rot = np.array([
            [cy_,       0,   sy],
            [sx * sy,  cx_, -sx * cy_],
            [-cx_ * sy, sx,  cx_ * cy_],
        ])

        # Rotate all 60 vertices
        rotated = _TV @ rot.T
        px = (rotated[:, 0] * r * 0.85 + cx).astype(int)
        py = (rotated[:, 1] * r * 0.85 + cy).astype(int)
        pz = rotated[:, 2]

        # White base circle
        if self._flash_timer > 0 and self._flash_color:
            cv2.circle(frame, (cx, cy), r, self._flash_color, -1)
        else:
            cv2.circle(frame, (cx, cy), r, (255, 255, 255), -1)

        # Sort faces by depth (painter's algorithm) — draw back-to-front
        face_list = []
        for face in _HF:
            z = np.mean(pz[face])
            if z > -0.2:
                pts = np.array([[px[i], py[i]] for i in face], dtype=np.int32)
                face_list.append((z, pts, (255, 255, 255)))  # white hexagons
        for face in _PF:
            z = np.mean(pz[face])
            if z > -0.2:
                pts = np.array([[px[i], py[i]] for i in face], dtype=np.int32)
                face_list.append((z, pts, (30, 30, 30)))  # dark pentagons

        face_list.sort(key=lambda f: f[0])
        for _, pts, color in face_list:
            cv2.fillPoly(frame, [pts], color)

        # Seam lines (front-facing edges only)
        for i, j in _TE:
            if pz[i] > -0.1 and pz[j] > -0.1:
                cv2.line(frame, (px[i], py[i]), (px[j], py[j]), (80, 80, 80), 1)

        # Black outline
        cv2.circle(frame, (cx, cy), r, (0, 0, 0), 2)
