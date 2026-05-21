import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "webotsvs"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "methods"))

_WEBOTS_PYTHON = "/Applications/Webots.app/Contents/lib/controller/python"
if os.path.isdir(_WEBOTS_PYTHON) and _WEBOTS_PYTHON not in sys.path:
    sys.path.insert(0, _WEBOTS_PYTHON)

from controller import Supervisor
from methods.ant_colony import ant_colony
from obstacles import OBSTACLES, inflate_obstacles
from aux_points import auxiliary_points
from dijkstra import build_graph, dijkstra
from energy import edge_energy

TAKEOFF = 0
FLYING = 1
LANDING = 2

GROUND_HEIGHT = 0.0
WAYPOINT_HEIGHT = 1.0
FLIGHT_HEIGHT = WAYPOINT_HEIGHT
LANDING_SPEED = 0.5

START_X = 0.0
START_Y = 0.0

FIELD_HALF = 7.0
GRID_STEP = 1.5
SAFETY_DELTA = 0.3
Z_LEVELS = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0]

SAFETY = 0.4

K_UP = 2.0
K_DOWN = 0.5

def energy_weight(p1, p2):
    return edge_energy(p1, p2, K_UP, K_DOWN)

def read_waypoints(robot):
    points = []
    i = 0
    while True:
        node = robot.getFromDef("WP" + str(i))
        if node is None:
            break
        t = node.getField("translation").getSFVec3f()
        points.append((t[0], t[1], t[2]))
        i = i + 1
    return points

def remove_existing_obstacles(robot):
    i = 0
    while True:
        node = robot.getFromDef("OBS" + str(i))
        if node is None:
            break
        node.remove()
        i = i + 1


def add_obstacle_nodes(robot, obstacles):
    children = robot.getRoot().getField("children")
    for i in range(len(obstacles)):
        obs = obstacles[i]
        if obs["type"] == "box":
            cx = (obs["x_min"] + obs["x_max"]) / 2.0
            cy = (obs["y_min"] + obs["y_max"]) / 2.0
            cz = (obs["z_min"] + obs["z_max"]) / 2.0
            sx = obs["x_max"] - obs["x_min"]
            sy = obs["y_max"] - obs["y_min"]
            sz = obs["z_max"] - obs["z_min"]
            node_str = (
                "DEF OBS" + str(i) + " Solid {"
                " translation " + str(cx) + " " + str(cy) + " " + str(cz) +
                " children [ Shape {"
                " appearance PBRAppearance { baseColor 0.55 0.4 0.25 roughness 0.8 }"
                " geometry Box { size " + str(sx) + " " + str(sy) + " " + str(sz) + " }"
                " } ]"
                " name \"obs" + str(i) + "\""
                " }"
            )
        elif obs["type"] == "cylinder":
            cz = (obs["z_min"] + obs["z_max"]) / 2.0
            h = obs["z_max"] - obs["z_min"]
            node_str = (
                "DEF OBS" + str(i) + " Solid {"
                " translation " + str(obs["x"]) + " " + str(obs["y"]) + " " + str(cz) +
                " children [ Shape {"
                " appearance PBRAppearance { baseColor 0.45 0.3 0.18 roughness 0.85 }"
                " geometry Cylinder { height " + str(h) + " radius " + str(obs["r"]) + " }"
                " } ]"
                " name \"obs" + str(i) + "\""
                " }"
            )
        else:
            continue
        children.importMFNodeFromString(-1, node_str)


def main():
    robot = Supervisor()
    timestep = int(robot.getBasicTimeStep())

    points = read_waypoints(robot)

    remove_existing_obstacles(robot)
    add_obstacle_nodes(robot, OBSTACLES)
    inflated_obstacles = inflate_obstacles(OBSTACLES, SAFETY)

    field_x_min = -FIELD_HALF
    field_x_max =  FIELD_HALF
    field_y_min = -FIELD_HALF
    field_y_max =  FIELD_HALF

    aux = auxiliary_points(
        x_min=field_x_min, x_max=field_x_max,
        y_min=field_y_min, y_max=field_y_max,
        h_x=GRID_STEP, h_y=GRID_STEP,
        delta=SAFETY_DELTA,
        obstacles=inflated_obstacles,
        z_levels=Z_LEVELS,
    )

    n = len(points)
    nodes = []
    for p in points:
        nodes.append((p[0], p[1], FLIGHT_HEIGHT))
    nodes.append((START_X, START_Y, FLIGHT_HEIGHT))
    
    start_idx = n
    for a in aux:
        nodes.append(a)
    edges = build_graph(nodes, inflated_obstacles, weight_fn=energy_weight)
    
    dist = []
    for i in range(n):
        dist.append([0.0] * n)
    paths_wp = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d, idx_path = dijkstra(edges, i, j)
            if not idx_path:
                d = 999999
                idx_path = [i, j]
            dist[i][j] = d
            paths_wp[(i, j)] = idx_path

    paths_from_start = {}
    paths_to_start = {}
    for i in range(n):
        _, idx_path = dijkstra(edges, start_idx, i)
        if not idx_path:
            idx_path = [start_idx, i]
        paths_from_start[i] = idx_path
        _, idx_path = dijkstra(edges, i, start_idx)
        if not idx_path:
            idx_path = [i, start_idx]
        paths_to_start[i] = idx_path

    tour = ant_colony(dist)

    flight_path = [] 
    def append_idx_path(idx_path, dest_label):
        for k in range(1, len(idx_path)):
            nx, ny, nz = nodes[idx_path[k]]
            is_wp = (k == len(idx_path) - 1)
            label = dest_label if is_wp else None
            flight_path.append((nx, ny, nz, is_wp, label))

    append_idx_path(paths_from_start[tour[0]], "wp" + str(tour[0]))
    for k in range(len(tour) - 1):
        i = tour[k]
        j = tour[k + 1]
        append_idx_path(paths_wp[(i, j)], "wp" + str(j))
    append_idx_path(paths_to_start[tour[-1]], "start")


    def euclid3(p1, p2):
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        dz = p1[2] - p2[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def path_metric_length(idx_path):
        total = 0.0
        for k in range(len(idx_path) - 1):
            total += euclid3(nodes[idx_path[k]], nodes[idx_path[k + 1]])
        return total

    def path_energy(idx_path):
        total = 0.0
        for k in range(len(idx_path) - 1):
            total += energy_weight(nodes[idx_path[k]], nodes[idx_path[k + 1]])
        return total

    seq = [start_idx] + list(tour) + [start_idx]

    direct_length = 0.0
    for k in range(len(seq) - 1):
        direct_length += euclid3(nodes[seq[k]], nodes[seq[k + 1]])

    real_length = path_metric_length(paths_from_start[tour[0]])
    for k in range(len(tour) - 1):
        real_length += path_metric_length(paths_wp[(tour[k], tour[k + 1])])
    real_length += path_metric_length(paths_to_start[tour[-1]])

    total_energy = path_energy(paths_from_start[tour[0]])
    for k in range(len(tour) - 1):
        total_energy += path_energy(paths_wp[(tour[k], tour[k + 1])])
    total_energy += path_energy(paths_to_start[tour[-1]])

    if direct_length > 0:
        overhead_pct = (real_length - direct_length) / direct_length * 100.0
    else:
        overhead_pct = 0.0

    
    line = "=" * 60
    print("")
    print(line)
    print("              РЕЗУЛЬТАТИ ПЛАНУВАННЯ МАРШРУТУ")
    print(line)
    print("  Кількість точок (WP)         : {}".format(n))
    print("  Кількість перешкод           : {}".format(len(OBSTACLES)))
    print("  Вузлів графа (WP + start + aux): {}".format(len(nodes)))
    print("  Сегментів польоту            : {}".format(len(flight_path)))
    print("-" * 60)
    print("  Порядок обходу (ACO):")
    print("    start -> " + " -> ".join("wp" + str(t) for t in tour) + " -> start")
    print("-" * 60)
    print("  Пряма довжина (без обходу)   : {:8.3f} ум. од. довж.".format(direct_length))
    print("  Реальна довжина (з обходом)  : {:8.3f} ум. од. довж.".format(real_length))
    print("  Подовження через перешкоди   : {:+7.2f} %".format(overhead_pct))
    print("-" * 60)
    print("  Енергія туру                 : {:8.3f} ум. од.".format(total_energy))
    print("  Енергія / реальна довжина    : {:8.3f} ум. од./ум. од. довж.".format(
        total_energy / real_length if real_length > 0 else 0.0))
    print("  Коефіцієнти                  : k_up={}, k_down={}".format(K_UP, K_DOWN))
    print(line)
    print("")

    agent_node = robot.getSelf()
    translation_field = agent_node.getField("translation")

    speed = 1.0
    pos_x = START_X
    pos_y = START_Y
    pos_z = GROUND_HEIGHT
    translation_field.setSFVec3f([pos_x, pos_y, pos_z])

    cur_seg = 0
    flight_state = TAKEOFF

    while robot.step(timestep) != -1:
        if flight_state == TAKEOFF:
            if pos_z < FLIGHT_HEIGHT:
                pos_z += LANDING_SPEED * timestep / 1000.0
                if pos_z >= FLIGHT_HEIGHT:
                    pos_z = FLIGHT_HEIGHT
                    flight_state = FLYING
                    print("Підйом завершено, починаю політ")
            translation_field.setSFVec3f([pos_x, pos_y, pos_z])

        elif flight_state == FLYING:
            if cur_seg >= len(flight_path):
                flight_state = LANDING
                print("Усі точки відвідано, починаю посадку")
                continue
            seg_x, seg_y, seg_z, is_wp, label = flight_path[cur_seg]
            target_z = seg_z

            dx = seg_x - pos_x
            dy = seg_y - pos_y
            dz = target_z - pos_z
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            step_dist = speed * timestep / 1000.0

            if d <= step_dist:
                pos_x = seg_x
                pos_y = seg_y
                pos_z = target_z
                if is_wp:
                    if label == "start":
                        print("Повернувся на старт")
                    else:
                        print("Прибув у " + str(label))
                cur_seg = cur_seg + 1
            else:
                pos_x = pos_x + dx / d * step_dist
                pos_y = pos_y + dy / d * step_dist
                pos_z = pos_z + dz / d * step_dist

            translation_field.setSFVec3f([pos_x, pos_y, pos_z])

        elif flight_state == LANDING:
            if pos_z > GROUND_HEIGHT:
                pos_z -= LANDING_SPEED * timestep / 1000.0
                if pos_z <= GROUND_HEIGHT:
                    pos_z = GROUND_HEIGHT
                    print("Посадка завершена")
                    break
            translation_field.setSFVec3f([pos_x, pos_y, pos_z])


main()
