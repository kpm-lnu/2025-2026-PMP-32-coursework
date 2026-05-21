import os
import sys
import time

from points import generate_points, distance_matrix, tour_length
from nearest_neighbor import nearest_neighbor
from nearest_insertion import nearest_insertion
from ant_colony import ant_colony

def print_table(title, results):
    print("=" * 95)
    print(title)
    print("=" * 95)
    print("  N  | Найближчий сусід  | Найближче вставлення | Мурашина колонія")
    print("     | довжина     час   | довжина        час   | довжина     час")
    print("-" * 95)
    for r in results:
        n, l1, t1, l2, t2, l3, t3 = r
        print(
            " " + str(n).rjust(3) + " | " +
            str(round(l1, 2)).rjust(7) + " " + str(round(t1, 5)).rjust(8) + " | " +
            str(round(l2, 2)).rjust(7) + " " + str(round(t2, 5)).rjust(11) + " | " +
            str(round(l3, 2)).rjust(7) + " " + str(round(t3, 5)).rjust(8)
        )
    print("=" * 95)

def main():
    sizes = [10, 20, 30, 40, 50, 60]

    results = []

    for n in sizes:
        points = generate_points(n)
        dist = distance_matrix(points)

        t1 = time.perf_counter()
        tour1 = nearest_neighbor(dist)
        time1 = time.perf_counter() - t1
        length1 = tour_length(tour1, dist)

        t2 = time.perf_counter()
        tour2 = nearest_insertion(dist)
        time2 = time.perf_counter() - t2
        length2 = tour_length(tour2, dist)

        t3 = time.perf_counter()
        tour3 = ant_colony(dist)
        time3 = time.perf_counter() - t3
        length3 = tour_length(tour3, dist)

        results.append((n, length1, time1, length2, time2, length3, time3))

    print_table("Результати", results)

main()
