import cv2
import os
import numpy as np
from config import IMG_DIR


def extract_colors(views, img_files, all_points_3d):
    colors_all = np.zeros((len(all_points_3d), 3))

    for v_idx, v in enumerate(views):
        img_path = os.path.join(IMG_DIR, img_files[v_idx])
        img = cv2.imread(img_path)
        if img is None: continue

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) / 255.0




        for kp_idx, p3d_idx in enumerate(v['kp_to_3d']):
            if p3d_idx == -1 or np.any(colors_all[p3d_idx] != 0):
                continue
            x, y = v['kp'][kp_idx].pt
            x, y = int(round(x)), int(round(y))
            if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
                colors_all[p3d_idx] = img[y, x]
    return colors_all