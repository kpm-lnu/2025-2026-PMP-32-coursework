import math
import heapq

def euclid(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    dz = p1[2] - p2[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)

def segment_intersects_box(p1, p2, x_min, x_max, y_min, y_max, z_min, z_max):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    p_dirs = [-dx, dx, -dy, dy, -dz, dz]
    q_dists = [
        p1[0] - x_min, x_max - p1[0],
        p1[1] - y_min, y_max - p1[1],
        p1[2] - z_min, z_max - p1[2],
    ]

    t0 = 0.0
    t1 = 1.0
    for i in range(6):
        p = p_dirs[i]
        q = q_dists[i]
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                if t > t1:
                    return False
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return False
                if t < t1:
                    t1 = t
    return t0 <= t1


def segment_intersects_cylinder(p1, p2, cx, cy, r, z_min, z_max):
    
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    fx = p1[0] - cx
    fy = p1[1] - cy

    a = dx * dx + dy * dy
    b = 2.0 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - r * r

    if a == 0:
        if c > 0:
            return False
        tx_lo = -math.inf
        tx_hi = math.inf
    else:
        disc = b * b - 4.0 * a * c
        if disc < 0:
            return False
        sq = math.sqrt(disc)
        tx_lo = (-b - sq) / (2.0 * a)
        tx_hi = (-b + sq) / (2.0 * a)

    if dz == 0:
        if p1[2] < z_min or p1[2] > z_max:
            return False
        tz_lo = -math.inf
        tz_hi = math.inf
    else:
        t_at_zmin = (z_min - p1[2]) / dz
        t_at_zmax = (z_max - p1[2]) / dz
        if t_at_zmin <= t_at_zmax:
            tz_lo = t_at_zmin
            tz_hi = t_at_zmax
        else:
            tz_lo = t_at_zmax
            tz_hi = t_at_zmin

    t_lo = max(0.0, tx_lo, tz_lo)
    t_hi = min(1.0, tx_hi, tz_hi)
    return t_lo <= t_hi

def segment_intersects_obstacle(p1, p2, obs):
    if obs["type"] == "box":
        return segment_intersects_box(
            p1, p2,
            obs["x_min"], obs["x_max"],
            obs["y_min"], obs["y_max"],
            obs["z_min"], obs["z_max"],
        )
    if obs["type"] == "cylinder":
        return segment_intersects_cylinder(
            p1, p2, obs["x"], obs["y"], obs["r"], obs["z_min"], obs["z_max"]
        )
    return False

def _point_in_obs(p, obs):
    if obs["type"] == "box":
        return (obs["x_min"] <= p[0] <= obs["x_max"] and
                obs["y_min"] <= p[1] <= obs["y_max"] and
                obs["z_min"] <= p[2] <= obs["z_max"])
    if obs["type"] == "cylinder":
        if p[2] < obs["z_min"] or p[2] > obs["z_max"]:
            return False
        dx = p[0] - obs["x"]
        dy = p[1] - obs["y"]
        return dx * dx + dy * dy <= obs["r"] * obs["r"]
    return False

def segment_clear(p1, p2, obstacles):
    for obs in obstacles:
        if _point_in_obs(p1, obs) or _point_in_obs(p2, obs):
            return False
        if segment_intersects_obstacle(p1, p2, obs):
            return False
    return True

def build_graph(nodes, obstacles, weight_fn=None):
    if weight_fn is None:
        weight_fn = euclid
    n = len(nodes)
    edges = []
    for i in range(n):
        edges.append([])
    for i in range(n):
        for j in range(i + 1, n):
            if segment_clear(nodes[i], nodes[j], obstacles):
                w = weight_fn(nodes[i], nodes[j])
                edges[i].append((j, w))
                edges[j].append((i, w))
    return edges

def dijkstra(edges, start, target):
    n = len(edges)
    inf = float("inf")
    dist = [inf] * n
    prev = [-1] * n
    dist[start] = 0.0
    pq = [(0.0, start)]

    while pq:
        d, u = heapq.heappop(pq)
        if u == target:
            break
        if d > dist[u]:
            continue
        for v, w in edges[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    if dist[target] == inf:
        return inf, []

    path = []
    u = target
    while u != -1:
        path.append(u)
        u = prev[u]
    path.reverse()
    return dist[target], path


