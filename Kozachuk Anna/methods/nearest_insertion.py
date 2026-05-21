def nearest_insertion(dist):
    n = len(dist)
    in_tour = [False] * n

    in_tour[0] = True
    nearest = -1
    min_dist = 999999
    for j in range(1, n):
        if dist[0][j] < min_dist:
            min_dist = dist[0][j]
            nearest = j

    tour = [0, nearest]
    in_tour[nearest] = True

    while len(tour) < n:
        next_city = -1
        min_dist = 999999
        for j in range(n):
            if in_tour[j] == False:
                for k in tour:
                    if dist[j][k] < min_dist:
                        min_dist = dist[j][k]
                        next_city = j

        best_pos = 0
        best_increase = 999999
        for i in range(len(tour)):
            a = tour[i]
            if i + 1 < len(tour):
                b = tour[i + 1]
            else:
                b = tour[0]
            increase = dist[a][next_city] + dist[next_city][b] - dist[a][b]
            if increase < best_increase:
                best_increase = increase
                best_pos = i + 1

        tour.insert(best_pos, next_city)
        in_tour[next_city] = True

    return tour
