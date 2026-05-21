import numpy as np

IMG_DIR = 'imgs/dino/'
INTRINSIC = np.array([
    [2360, 0, 320],
    [0, 2360, 240],
    [0, 0, 1]], dtype=np.float32)

K_INV = np.linalg.inv(INTRINSIC)