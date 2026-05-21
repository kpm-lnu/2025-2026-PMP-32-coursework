import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import config
import utils
import features
import triangulation
import colors
import visualization


def calculate_reprojection_error(p3d, p2d, P_ext, K):

    if len(p3d) == 0: return 0
    R = P_ext[:, :3]
    t = P_ext[:, 3:]
    rvec, _ = cv2.Rodrigues(R)
    projected_pts, _ = cv2.projectPoints(p3d.astype(np.float32), rvec, t, K, None)
    projected_pts = projected_pts.reshape(-1, 2)
    error = np.linalg.norm(projected_pts - p2d, axis=1)
    return np.mean(error)


def main():
    img_files = sorted([f for f in os.listdir(config.IMG_DIR) if f.lower().endswith(('.ppm', '.jpg', '.png'))])
    sift, flann = features.get_features_detector()

    all_points_3d = []
    views = []
    errors_history = [] # for errors
    points_added_history = [] # for points

    print(f"--- start processing {len(img_files)} imgs ---")

    for i, img_file in enumerate(img_files):
        img_path = os.path.join(config.IMG_DIR, img_file)
        img = cv2.imread(img_path)
        if img is None: continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kp, des = sift.detectAndCompute(gray, None)

        current_view = {
            'kp': kp,
            'des': des,
            'kp_to_3d': np.full(len(kp), -1, dtype=int),
            'P_ext': None
        }

        if i == 0:
            current_view['P_ext'] = np.eye(3, 4, dtype=np.float32)
            views.append(current_view)
            errors_history.append(0)
            points_added_history.append(0)
            print(f"[{i}] {img_file}: the base frame is set.")
            continue

        prev_view = views[i - 1]
        good = features.match_features(flann, prev_view['des'], current_view['des'])

        if i == 1:
            src_pts = np.float32([prev_view['kp'][m.queryIdx].pt for m in good])
            dst_pts = np.float32([current_view['kp'][m.trainIdx].pt for m in good])

            E, mask_e = cv2.findEssentialMat(src_pts, dst_pts, config.INTRINSIC, method=cv2.RANSAC, threshold=1.0)
            _, R, t, mask_p = cv2.recoverPose(E, src_pts, dst_pts, config.INTRINSIC, mask=mask_e)

            current_view['P_ext'] = np.hstack((R, t))
            idx_inliers = np.where(mask_p.ravel() == 1)[0]

            pts1_n = config.K_INV @ utils.cart2hom(src_pts[idx_inliers])
            pts2_n = config.K_INV @ utils.cart2hom(dst_pts[idx_inliers])
            pts3d = triangulation.linear_triangulation(pts1_n, pts2_n, prev_view['P_ext'], current_view['P_ext'])

            err = calculate_reprojection_error(pts3d[:3, :].T, dst_pts[idx_inliers], current_view['P_ext'],
                                               config.INTRINSIC)
            errors_history.append(err)

            added_count = 0
            for idx_in, original_idx in enumerate(idx_inliers):
                all_points_3d.append(pts3d[:3, idx_in])
                g_idx = len(all_points_3d) - 1
                m = good[original_idx]
                prev_view['kp_to_3d'][m.queryIdx] = g_idx
                current_view['kp_to_3d'][m.trainIdx] = g_idx
                added_count += 1

            points_added_history.append(added_count)
            print(f"[{i}] {img_file}: initialization. inlayers: {len(idx_inliers)}, error: {err:.4f} px")

        else:
            pts_3d_pnp, pts_2d_pnp, pnp_matches = [], [], []
            for m in good:
                if prev_view['kp_to_3d'][m.queryIdx] != -1:
                    pts_3d_pnp.append(all_points_3d[prev_view['kp_to_3d'][m.queryIdx]])
                    pts_2d_pnp.append(current_view['kp'][m.trainIdx].pt)
                    pnp_matches.append(m)

            pnp_err = 0
            num_inliers = 0
            if len(pts_3d_pnp) >= 10:
                success, rvec, tvec, inliers = cv2.solvePnPRansac(
                    np.array(pts_3d_pnp, dtype=np.float32), np.array(pts_2d_pnp, dtype=np.float32),
                    config.INTRINSIC, None)
                if success:
                    R, _ = cv2.Rodrigues(rvec)
                    current_view['P_ext'] = np.hstack((R, tvec))
                    if inliers is not None:
                        num_inliers = len(inliers)
                        inlier_pts3d = np.array(pts_3d_pnp)[inliers.ravel()]
                        inlier_pts2d = np.array(pts_2d_pnp)[inliers.ravel()]
                        pnp_err = calculate_reprojection_error(inlier_pts3d, inlier_pts2d, current_view['P_ext'],
                                                               config.INTRINSIC)
                        for idx in inliers.ravel():
                            m = pnp_matches[idx]
                            current_view['kp_to_3d'][m.trainIdx] = prev_view['kp_to_3d'][m.queryIdx]

            errors_history.append(pnp_err)


            new_pts_prev, new_pts_curr, new_matches = [], [], []
            for m in good:
                if prev_view['kp_to_3d'][m.queryIdx] == -1:
                    new_pts_prev.append(prev_view['kp'][m.queryIdx].pt)
                    new_pts_curr.append(current_view['kp'][m.trainIdx].pt)
                    new_matches.append(m)

            added_points = 0
            if len(new_pts_prev) > 0 and current_view['P_ext'] is not None:
                p_prev_n = config.K_INV @ utils.cart2hom(np.array(new_pts_prev))
                p_curr_n = config.K_INV @ utils.cart2hom(np.array(new_pts_curr))
                new_tri = triangulation.linear_triangulation(p_prev_n, p_curr_n, prev_view['P_ext'],
                                                             current_view['P_ext'])
                for idx in range(new_tri.shape[1]):
                    if new_tri[2, idx] > 0:
                        all_points_3d.append(new_tri[:3, idx])
                        current_view['kp_to_3d'][new_matches[idx].trainIdx] = len(all_points_3d) - 1
                        added_points += 1

            points_added_history.append(added_points)
            print(
                f"[{i}] {img_file}: PnP Inliers: {num_inliers}, error: {pnp_err:.4f} px, count of added points: {added_points}")

        views.append(current_view)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    fig.tight_layout(pad=5.0)

    ax1.plot(range(len(errors_history)), errors_history, marker='o', linestyle='-', color='maroon',
             label='Reprojection Error')
    ax1.set_title('frame-by-frame reprojection error graph')
    ax1.set_xlabel('number of frame')
    ax1.set_ylabel('avg error (px)')
    ax1.grid(True)
    ax1.legend()

    ax2.bar(range(len(points_added_history)), points_added_history, color='teal', alpha=0.7, label='New 3D Points')
    ax2.set_title('Number of new 3D points added on each frame')
    ax2.set_xlabel('number of frame')
    ax2.set_ylabel('count of points')
    ax2.grid(True, axis='y')
    ax2.legend()

    plt.savefig('reconstruction_stats.png')
    print("\n 'reconstruction_stats.png'")
    plt.show()

    points_3d_np = np.array(all_points_3d)
    colors_np = colors.extract_colors(views, img_files, points_3d_np)
    cam_path = np.array([utils.get_camera_center(v['P_ext']) for v in views if v['P_ext'] is not None])
    visualization.visualize_sfm(points_3d_np, colors_np, cam_path)


if __name__ == "__main__":
    main()