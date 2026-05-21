import math

def build_grid_2d(x_min, x_max, y_min, y_max, h_x, h_y):
    n_x = int(math.floor((x_max - x_min) / h_x))
    n_y = int(math.floor((y_max - y_min) / h_y))
    grid = []
    for i in range(n_x + 1):
        x_i = x_min + i * h_x
        for j in range(n_y + 1):
            y_j = y_min + j * h_y
            grid.append((x_i, y_j))
    return grid

def point_in_obstacle(x, y, z, obs):
    if obs["type"] == "box":
        return (obs["x_min"] <= x <= obs["x_max"] and
                obs["y_min"] <= y <= obs["y_max"] and
                obs["z_min"] <= z <= obs["z_max"])
    if obs["type"] == "cylinder":
        if z < obs["z_min"] or z > obs["z_max"]:
            return False
        dx = x - obs["x"]
        dy = y - obs["y"]
        return dx * dx + dy * dy <= obs["r"] * obs["r"]
    return False

def in_any_obstacle(x, y, z, obstacles):
    for obs in obstacles:
        if point_in_obstacle(x, y, z, obs):
            return True
    return False

def corner_points_box(obs, delta):
    return [
        (obs["x_min"] - delta, obs["y_min"] - delta),
        (obs["x_min"] - delta, obs["y_max"] + delta),
        (obs["x_max"] + delta, obs["y_min"] - delta),
        (obs["x_max"] + delta, obs["y_max"] + delta),
    ]

def in_field(x, y, x_min, x_max, y_min, y_max):
    return x_min <= x <= x_max and y_min <= y <= y_max

def auxiliary_points(x_min, x_max, y_min, y_max, h_x, h_y, delta, obstacles, z_levels):
    
    grid_2d = build_grid_2d(x_min, x_max, y_min, y_max, h_x, h_y)
    h_aux = []
    for z in z_levels:
        for (x, y) in grid_2d:
            if not in_any_obstacle(x, y, z, obstacles):
                h_aux.append((x, y, z))
        for obs in obstacles:
            if obs["type"] != "box":
                continue
            if z < obs["z_min"] or z > obs["z_max"]:
                continue
            for (cx, cy) in corner_points_box(obs, delta):
                if not in_field(cx, cy, x_min, x_max, y_min, y_max):
                    continue
                if in_any_obstacle(cx, cy, z, obstacles):
                    continue
                h_aux.append((cx, cy, z))
    return h_aux
