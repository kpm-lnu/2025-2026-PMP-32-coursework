import random
from typing import List

from points import tour_length


def ant_colony(dist: List[List[float]]) -> List[int]:
    n = len(dist)
    n_ants = 20
    n_iterations = 100
    alpha = 1.0
    beta = 5.0
    evaporation = 0.5
    q = 100.0

    pheromone = []
    for i in range(n):
        row = [1.0] * n
        pheromone.append(row)

    best_tour = []
    best_length = 999999

    for iteration in range(n_iterations):
        all_tours = []
        all_lengths = []

        for ant in range(n_ants):
            start = 0
            tour = [start]
            visited = [False] * n
            visited[start] = True
            current = start

            for step in range(n - 1):
                weights = []
                candidates = []
                for j in range(n):
                    if visited[j] == False:
                        if dist[current][j] > 0:
                            eta = 1.0 / dist[current][j]
                        else:
                            eta = 0
                        w = (pheromone[current][j] ** alpha) * (eta ** beta)
                        weights.append(w)
                        candidates.append(j)

                total = 0
                for w in weights:
                    total = total + w

                if total == 0:
                    next_city = random.choice(candidates)
                else:
                    r = random.random() * total
                    acc = 0
                    next_city = candidates[0]
                    for i in range(len(candidates)):
                        acc = acc + weights[i]
                        if acc >= r:
                            next_city = candidates[i]
                            break

                tour.append(next_city)
                visited[next_city] = True
                current = next_city

            length = tour_length(tour, dist)
            all_tours.append(tour)
            all_lengths.append(length)

            if length < best_length:
                best_length = length
                best_tour = list(tour)

        for i in range(n):
            for j in range(n):
                pheromone[i][j] = pheromone[i][j] * (1.0 - evaporation)

        for k in range(len(all_tours)):
            tour = all_tours[k]
            length = all_lengths[k]
            deposit = q / length
            for i in range(n):
                a = tour[i]
                if i + 1 < n:
                    b = tour[i + 1]
                else:
                    b = tour[0]
                pheromone[a][b] = pheromone[a][b] + deposit
                pheromone[b][a] = pheromone[b][a] + deposit

    return best_tour
