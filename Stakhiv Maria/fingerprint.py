import cv2
import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
import os
import sqlite3
import json

def filter_minutiae(minutiae, min_distance=12):
    if len(minutiae) == 0: return np.array([])
    filtered = []
    for m in minutiae:
        if not filtered:
            filtered.append(m)
            continue
        pts = np.array([f[:2] for f in filtered])
        curr = np.array(m[:2])
        dists = np.linalg.norm(pts - curr, axis=1)
        if np.min(dists) >= min_distance:
            filtered.append(m)
    return np.array(filtered)

def get_minutiae_and_skeleton(image_path, margin=40):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Файл {image_path} не знайдено!")
        
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    binary_bool = binary > 0
    skeleton = skeletonize(binary_bool).astype(np.uint8)
    
    raw_minutiae = []
    rows, cols = skeleton.shape
    for i in range(margin, rows - margin):
        for j in range(margin, cols - margin):
            if skeleton[i, j] == 1:
                p = [int(skeleton[i-1, j-1]), int(skeleton[i-1, j]), int(skeleton[i-1, j+1]),
                     int(skeleton[i, j+1]), int(skeleton[i+1, j+1]), int(skeleton[i+1, j]),
                     int(skeleton[i+1, j-1]), int(skeleton[i, j-1])]
                transitions = sum(abs(p[k] - p[k-1]) for k in range(8)) // 2
                
                if transitions == 1: raw_minutiae.append([j, i, 1]) 
                elif transitions == 3: raw_minutiae.append([j, i, 3]) 
                    
    filtered_minutiae = filter_minutiae(raw_minutiae, min_distance=12)
    return filtered_minutiae, skeleton, img

def build_delaunay_triangulation(points):
    coords = points[:, :2]
    if len(coords) < 3:
        raise ValueError("Недостатньо точок.")
    return Delaunay(coords)

def get_triangle_features(points, tri, min_edge=10, max_edge=80):
    features = []
    for simplex in tri.simplices:
        pts = points[simplex] 
        
        l0 = np.linalg.norm(pts[1][:2] - pts[2][:2]) 
        l1 = np.linalg.norm(pts[0][:2] - pts[2][:2]) 
        l2 = np.linalg.norm(pts[0][:2] - pts[1][:2]) 
        
        if max(l0, l1, l2) > max_edge or min(l0, l1, l2) < min_edge:
            continue
            
        edges = [
            (l0, 0, pts[1][2], pts[2][2]),
            (l1, 1, pts[0][2], pts[2][2]),
            (l2, 2, pts[0][2], pts[1][2])
        ]
        
        edges.sort(key=lambda x: x[0]) 
        
        if abs(edges[0][0] - edges[1][0]) < 1.0 or abs(edges[1][0] - edges[2][0]) < 1.0:
            continue
            
        idx_longest = edges[2][1]
        idx_mid = edges[1][1]
        
        vec = pts[idx_mid][:2] - pts[idx_longest][:2]
        angle = np.degrees(np.arctan2(vec[1], vec[0])) 
        
        features.append({
            'lengths': [float(e[0]) for e in edges],
            'types_pairs': [(int(min(e[2], e[3])), int(max(e[2], e[3]))) for e in edges],
            'angle': float(angle),
            'simplex': [int(x) for x in simplex]
        })
    return features

def match_fingerprints(features1, features2, tolerance=3.0):
    raw_matches = []
    
    for f1 in features1:
        best_match_idx = -1
        best_match_diff = float('inf')
        
        for i, f2 in enumerate(features2):
            if f1['types_pairs'] == f2['types_pairs']:
                arr_f1 = np.array(f1['lengths'])
                arr_f2 = np.array(f2['lengths'])
                
                diffs = np.abs(arr_f1 - arr_f2)
                if np.all(diffs < tolerance):
                    total_diff = np.sum(diffs)
                    if total_diff < best_match_diff:
                        best_match_diff = total_diff
                        best_match_idx = i
                        
        if best_match_idx != -1:
            angle_diff = (f1['angle'] - features2[best_match_idx]['angle']) % 360
            if angle_diff > 180: angle_diff -= 360
                
            raw_matches.append({
                'idx2': best_match_idx,
                'angle_diff': angle_diff,
                'simplex1': f1['simplex'],
                'simplex2': features2[best_match_idx]['simplex']
            })
            
    if not raw_matches:
        return 0, 0.0, [], []

    angle_diffs = [m['angle_diff'] for m in raw_matches]
    bins = np.arange(-180, 181, 20) 
    hist, bin_edges = np.histogram(angle_diffs, bins=bins)
    
    max_bin_idx = np.argmax(hist) 
    dominant_angle = (bin_edges[max_bin_idx] + bin_edges[max_bin_idx+1]) / 2
    
    valid_matches = []
    used_idx2 = set()
    for m in raw_matches:
        diff_to_center = abs((m['angle_diff'] - dominant_angle + 180) % 360 - 180)
        
        if diff_to_center <= 25.0 and m['idx2'] not in used_idx2:
            valid_matches.append(m)
            used_idx2.add(m['idx2'])
            
    match_count = len(valid_matches)
    max_possible = min(len(features1), len(features2))
    score = (match_count / max_possible * 100) if max_possible > 0 else 0
    
    mt1 = [m['simplex1'] for m in valid_matches]
    mt2 = [m['simplex2'] for m in valid_matches]
    
    return match_count, score, mt1, mt2

def visualize_comparison(img1, skel1, points1, tri1, mt1, title1, img2, skel2, points2, tri2, mt2, title2, score, is_same_person):
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    color = 'green' if is_same_person else 'red'
    status = "УСПІШНА (Розпізнано з БД)" if is_same_person else "ВІДХИЛЕНА (Невідома особа або інший палець)"
    
    fig.suptitle(f"ІДЕНТИФІКАЦІЯ У БАЗІ ДАНИХ\n{status} (Score: {score:.1f}%)", fontsize=16, fontweight='bold', color=color)

    for col, (img, skel, points, tri, matched_tris, title) in enumerate([(img1, skel1, points1, tri1, mt1, title1), (img2, skel2, points2, tri2, mt2, title2)]):
        ax = axs[0, col]
        ax.imshow(img, cmap='gray')
        coords = points[:, :2]
        if tri is not None:
            ax.triplot(coords[:, 0], coords[:, 1], tri.simplices.copy(), color='cyan', linewidth=0.5, alpha=0.4)
        
        for simplex in matched_tris:
            pts = coords[simplex]
            cx, cy = np.mean(pts, axis=0) 
            ax.plot(cx, cy, 'g+', markersize=12, markeredgewidth=2, zorder=10)
        
        ax.scatter(points[points[:, 2] == 1, 0], points[points[:, 2] == 1, 1], c='red', s=20, label='Закінчення', zorder=5)
        ax.scatter(points[points[:, 2] == 3, 0], points[points[:, 2] == 3, 1], c='blue', s=20, label='Роздвоєння', zorder=5)
        ax.set_title(f"{title}\nКількість точок: {len(points)}", fontsize=11)
        ax.axis('off')
        if col == 0: ax.legend(loc='lower right', fontsize='small')

        axs[1, col].imshow(skel * 255, cmap='gray')
        axs[1, col].set_title(f"Скелет: {title}")
        axs[1, col].axis('off')

    plt.tight_layout()
    plt.subplots_adjust(top=0.88) 
    plt.show()

DB_NAME = "biometrics.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Видаляємо стару таблицю, щоб додати колонку image_path
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            features_json TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def register_user(name, image_path):
    if not os.path.exists(image_path):
        print(f"⚠️ Файл {image_path} не знайдено.")
        return
        
    pts, _, _ = get_minutiae_and_skeleton(image_path)
    tri = build_delaunay_triangulation(pts)
    features = get_triangle_features(pts, tri)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    features_json = json.dumps(features) 
    cursor.execute('INSERT INTO users (name, features_json, image_path) VALUES (?, ?, ?)', (name, features_json, image_path))
    
    print(f"[БД] Користувача '{name}' успішно зареєстровано!")
    conn.commit()
    conn.close()

def identify_user_and_visualize(query_image_path, threshold=19.0):
    print(f"\n--- Сканування запиту: {query_image_path} ---")
    pts_query, skel_query, img_query = get_minutiae_and_skeleton(query_image_path)
    tri_query = build_delaunay_triangulation(pts_query)
    feat_query = get_triangle_features(pts_query, tri_query)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT name, features_json, image_path FROM users')
    
    best_match_name = None
    best_score = 0.0
    best_mt_db = []
    best_mt_query = []
    best_image_path = None
    
    for row in cursor.fetchall():
        name = row[0]
        db_features = json.loads(row[1]) 
        db_image_path = row[2]
        
        for f in db_features:
            f['types_pairs'] = [tuple(pair) for pair in f['types_pairs']]
        
        _, score, mt_db, mt_query = match_fingerprints(db_features, feat_query, tolerance=7.0)
        
        if score > best_score:
            best_score = score
            best_match_name = name
            best_mt_db = mt_db
            best_mt_query = mt_query
            best_image_path = db_image_path
            
    conn.close()
    
    is_same = best_score >= threshold
    
    if is_same:
        print(f"✅ ДОСТУП ДОЗВОЛЕНО: Знайдено збіг з '{best_match_name}' (Score: {best_score:.1f}%)")
    else:
        print(f"❌ ДОСТУП ЗАБОРОНЕНО: Особу не розпізнано (Найкращий збіг: {best_match_name} з {best_score:.1f}%)")

    # Безпечне підвантаження зображення БД для візуалізації
    if best_image_path and os.path.exists(best_image_path):
        pts_db, skel_db, img_db = get_minutiae_and_skeleton(best_image_path)
        tri_db = build_delaunay_triangulation(pts_db)
        title_db = f"БД: {best_match_name} ({best_image_path})"
    else:
        # Якщо в базі взагалі порожньо, малюємо пустий графік
        img_db, skel_db, pts_db, tri_db, title_db = img_query, skel_query, pts_query, tri_query, "БД: Не знайдено"

    visualize_comparison(img_db, skel_db, pts_db, tri_db, best_mt_db, title_db,
                         img_query, skel_query, pts_query, tri_query, best_mt_query, f"Запит: {query_image_path}",
                         best_score, is_same)

if __name__ == "__main__":
    
    THRESHOLD = 19.0

    print("--- ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ ---")
    init_db()
    
    print("\n--- ЕТАП МАСОВОЇ РЕЄСТРАЦІЇ ---")
    users_to_register = {
        "Суб'єкт 101": "101_1.tif",
        "Суб'єкт 102": "102_1.tif",
        "Суб'єкт 103": "103_1.tif",
        "Суб'єкт 104": "104_1.tif"
    }
    
    for name, path in users_to_register.items():
        register_user(name, path)

    print("\n\n=== ТЕСТ 1: Перевірка на успішний збіг (Той самий палець) ===")
    identify_user_and_visualize("104_2.tif", THRESHOLD)

    print("\n\n=== ТЕСТ 2: Перевірка на відмову (Інша людина) ===")
    identify_user_and_visualize("102_2.tif", THRESHOLD)

