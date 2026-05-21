import open3d as o3d
import numpy as np

def visualize_sfm(points_3d, colors, cam_path):
    # 1. create cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points_3d)
    pcd.colors = o3d.utility.Vector3dVector(colors)

    # 2. filter
    pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
    pcd, _ = pcd.remove_radius_outlier(nb_points=16, radius=0.05)

    # 3. camera trajectory
    geometries = [pcd]
    for pos in cam_path:
        sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.02)
        sphere.translate(pos)
        sphere.paint_uniform_color([1, 0, 0])
        geometries.append(sphere)

    # 4. points
    print("point cloud display...")
    o3d.visualization.draw_geometries([pcd])

    # 5. alpha shape
    alpha = 0.03
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
    mesh.compute_vertex_normals()
    print("displaying a 3D model (Mesh)...")
    o3d.visualization.draw_geometries([mesh], mesh_show_back_face=True)