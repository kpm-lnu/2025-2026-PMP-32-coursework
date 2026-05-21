import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from scipy.spatial import Delaunay
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

nx = 16
ny = 16

x = np.linspace(0, 1, nx)
y = np.linspace(0, 1, ny)

X, Y = np.meshgrid(x, y)

points = np.column_stack([X.flatten(), Y.flatten()])

triangulation = Delaunay(points)
triangles = triangulation.simplices

N = len(points)

def source_center(x, y):
    return 10 * np.exp(
        -20 * ((x - 0.5)**2 + (y - 0.5)**2)
    )

def source_two_centers(x, y):
    return (
        8 * np.exp(-30 * ((x - 0.3)**2 + (y - 0.3)**2))
        +
        8 * np.exp(-30 * ((x - 0.7)**2 + (y - 0.7)**2))
    )

def source_linear(x, y):
    return 5 * x

def source_sinusoidal(x, y):
    return 5 * np.sin(np.pi * x) * np.sin(np.pi * y)

experiments = [
    ("Центральне джерело", source_center),
    ("Два осередки інфекції", source_two_centers),
    ("Лінійне джерело", source_linear),
    ("Синусоїдальне джерело", source_sinusoidal)
]

for experiment_name, f in experiments:

    print("\n")
    print("=" * 60)
    print("ЕКСПЕРИМЕНТ:", experiment_name)
    print("=" * 60)

    K = lil_matrix((N, N))
    M = lil_matrix((N, N))
    F = np.zeros(N)

    M_ref = np.array([
        [2, 1, 1],
        [1, 2, 1],
        [1, 1, 2]
    ]) / 24

    grad_ref = np.array([
        [-1, -1],
        [ 1,  0],
        [ 0,  1]
    ])

    for tri_nodes in triangles:

        coords = points[tri_nodes]

        x1, y1 = coords[0]
        x2, y2 = coords[1]
        x3, y3 = coords[2]

        J = np.array([
            [x2 - x1, x3 - x1],
            [y2 - y1, y3 - y1]
        ])

        detJ = np.linalg.det(J)

        area = abs(detJ) / 2

        invJ = np.linalg.inv(J)

        grad = grad_ref @ invJ.T

        Ke = np.zeros((3, 3))

        for i in range(3):
            for j in range(3):
                Ke[i, j] = area * np.dot(
                    grad[i],
                    grad[j]
                )

        Me = detJ * M_ref

        xc = (x1 + x2 + x3) / 3
        yc = (y1 + y2 + y3) / 3

        f_value = f(xc, yc)

        Fe = np.ones(3) * f_value * area / 3

        for i in range(3):

            F[tri_nodes[i]] += Fe[i]

            for j in range(3):

                K[tri_nodes[i], tri_nodes[j]] += Ke[i, j]
                M[tri_nodes[i], tri_nodes[j]] += Me[i, j]

    A = K + M

    boundary = np.where(
        (points[:, 0] == 0)
        |
        (points[:, 0] == 1)
        |
        (points[:, 1] == 0)
        |
        (points[:, 1] == 1)
    )[0]

    for b in boundary:

        A[b, :] = 0
        A[:, b] = 0
        A[b, b] = 1

        F[b] = 0

    u = spsolve(A.tocsr(), F)

    center_index = np.argmin(
        np.sum((points - [0.5, 0.5])**2, axis=1)
    )

    print("Кількість вузлів:", N)
    print("Кількість трикутників:", len(triangles))

    print("\nМаксимальна концентрація:", np.max(u))
    print("Мінімальна концентрація:", np.min(u))

    print("\nL2-норма:", np.linalg.norm(u))

    print(
        "\nКонцентрація у центрі області:",
        u[center_index]
    )

    triang = tri.Triangulation(
        points[:, 0],
        points[:, 1],
        triangles
    )

    fig = plt.figure(figsize=(10, 7))

    ax = fig.add_subplot(111, projection='3d')

    surface = ax.plot_trisurf(
        triang,
        u,
        cmap='viridis'
    )

    ax.set_title(
        f"{experiment_name}"
    )

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("Концентрація")

    fig.colorbar(surface)

    plt.show()

    plt.figure(figsize=(8, 6))

    contour = plt.tricontourf(
        triang,
        u,
        20,
        cmap='viridis'
    )

    plt.colorbar(contour)

    plt.title(
        f"Контурна карта: {experiment_name}"
    )

    plt.xlabel("x")
    plt.ylabel("y")

    plt.show()

    plt.figure(figsize=(8, 8))

    plt.triplot(
        triang,
        linewidth=0.6,
        color='black'
    )

    plt.scatter(
        points[:, 0],
        points[:, 1],
        s=10
    )

    plt.title(
        f"Сітка FEM: {experiment_name}"
    )

    plt.xlabel("x")
    plt.ylabel("y")

    plt.gca().set_aspect('equal')

    plt.show()

    plt.figure(figsize=(8, 6))

    plt.tripcolor(
        triang,
        u,
        shading='gouraud',
        cmap='viridis'
    )

    plt.colorbar(label="Концентрація")

    plt.title(
        f"Теплова карта: {experiment_name}"
    )

    plt.xlabel("x")
    plt.ylabel("y")

    plt.show()

    center_mask = np.isclose(
        points[:, 1],
        0.5,
        atol=0.05
    )

    center_points = points[center_mask]
    center_values = u[center_mask]

    order = np.argsort(center_points[:, 0])

    center_points = center_points[order]
    center_values = center_values[order]

    plt.figure(figsize=(8, 5))

    plt.plot(
        center_points[:, 0],
        center_values,
        'o-'
    )

    plt.title(
        f"Профіль через центр: {experiment_name}"
    )

    plt.xlabel("x")
    plt.ylabel("Концентрація")

    plt.grid()

    plt.show()