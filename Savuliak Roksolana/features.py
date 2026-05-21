import cv2

def get_features_detector():
    sift = cv2.SIFT_create(nfeatures=5000)
    flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=100))
    return sift, flann

def match_features(flann, des1, des2):
    matches = flann.knnMatch(des1, des2, k=2)
    good = [m for m, n in matches if m.distance < 0.85 * n.distance]
    return good