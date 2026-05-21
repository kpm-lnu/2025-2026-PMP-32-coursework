import random
import math

def generate_points(n):
    points = []
    for i in range(n):
        x = random.uniform(0, 100)
        y = random.uniform(0, 100)
        z = random.uniform(0, 100)
        points.append((x, y, z))
    return points

def distance(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    dz = p1[2] - p2[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)

def distance_matrix(points):
    n = len(points)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(distance(points[i], points[j]))
        matrix.append(row)
    return matrix

def tour_length(tour, dist):
    total = 0
    for i in range(len(tour) - 1):
        total = total + dist[tour[i]][tour[i + 1]]
    total = total + dist[tour[-1]][tour[0]]
    return total