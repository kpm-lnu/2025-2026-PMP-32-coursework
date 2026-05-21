import numpy as np

def linear_triangulation(p1, p2, m1, m2):
    num_points = p1.shape[1]
    res = np.ones((4, num_points))
    for i in range(num_points):
        A = np.vstack([
            p1[0, i] * m1[2, :] - m1[0, :],
            p1[1, i] * m1[2, :] - m1[1, :],
            p2[0, i] * m2[2, :] - m2[0, :],
            p2[1, i] * m2[2, :] - m2[1, :]
        ])
        _, _, V = np.linalg.svd(A)
        X = V[-1, :4]
        res[:, i] = X / X[3]
    return res