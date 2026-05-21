import numpy as np

def cart2hom(pts):
    """[x, y] -> [x, y, 1]"""
    return np.vstack([pts.T, np.ones(pts.shape[0])])

def get_camera_center(P_ext):
    if P_ext is None:
        return None
    R = P_ext[:, :3]
    t = P_ext[:, 3:]
    return (-R.T @ t).ravel()