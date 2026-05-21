def nearest_neighbor(dist):
    n = len(dist)
    visited = [False] * n
    tour = [0]
    visited[0] = True
    current = 0

    for step in range(n - 1):
        nearest = -1
        min_dist = 999999

        for j in range(n):
            if visited[j] == False:
                if dist[current][j] < min_dist:
                    min_dist = dist[current][j]
                    nearest = j

        tour.append(nearest)
        visited[nearest] = True
        current = nearest

    return tour
