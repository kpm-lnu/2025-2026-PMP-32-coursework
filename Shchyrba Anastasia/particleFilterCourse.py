import cv2
import numpy as np

# ПАРАМЕТРИ
N = 500                  # кількість частинок
dt = 1.0                 # часовий крок між кадрами

Q_pos = 10.0             # шум позиції
Q_vel = 3.0              # шум швидкості
R_meas = 50.0            # шум вимірювання

WARMUP = 50              # кількість стартових кадрів без відображення траєкторії

# ВІДЕО
cap = cv2.VideoCapture("video/car_move_circle.mp4")
cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Tracking", 900, 800)

ret, frame = cap.read()
if not ret:
    print("Не вдалося відкрити відео")
    exit()

frame = cv2.resize(frame, (640, 480)) 
h, w = frame.shape[:2]

# ІНІЦІАЛІЗАЦІЯ ЧАСТИНОК
particles = np.zeros((N, 4))
particles[:, 0] = np.random.uniform(0, w, N)
particles[:, 1] = np.random.uniform(0, h, N)
particles[:, 2] = np.random.uniform(-5, 5, N)     
particles[:, 3] = np.random.uniform(-5, 5, N)

weights = np.ones(N) / N       

trajectory = []

# ВІДНІМАННЯ ФОНУ
bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=500,
    varThreshold=25,
    detectShadows=False
)

# ФУНКЦІЯ ПРОГНОЗУВАННЯ
def predict(particles):                           # формула руху: x' = x + v*dt + шум
    noise = np.random.multivariate_normal(          
        [0, 0, 0, 0],                             
        np.diag([Q_pos, Q_pos, Q_vel, Q_vel]),   
        N
    )

    particles[:, 0] += particles[:, 2] * dt
    particles[:, 1] += particles[:, 3] * dt

    particles += noise

    # обмеження координат
    particles[:, 0] = np.clip(particles[:, 0], 0, w)
    particles[:, 1] = np.clip(particles[:, 1], 0, h)

    return particles
   
# ОНОВЛЕННЯ ВАГ ЧАСТИНОК
def update(particles, weights, measurement):      # формула оцінки: w = exp(-||x - z||^2 / (2*R))
    if measurement is None:
        return np.ones(N) / N

    diff = particles[:, :2] - measurement
    dist = np.sum(diff**2, axis=1)

    weights = np.exp(-dist / (2 * R_meas))
    weights += 1e-300
    weights /= np.sum(weights)

    return weights

# ПЕРЕВИБІРКА ЧАСТИНОК
def resample(particles, weights):                
    cumulative_sum = np.cumsum(weights)     # накопичена сума ваг
    cumulative_sum[-1] = 1.0

    indexes = np.searchsorted(cumulative_sum, np.random.rand(N))

    particles = particles[indexes]
    weights = np.ones(N) / N

    return particles, weights

# ОЦІНКА СТАНУ ОБ'ЄКТА
def estimate(particles, weights):
    return np.average(particles, weights=weights, axis=0)

# ФОРМУВАННЯ ОБЛАСТІ ПОШУКУ
def get_bbox(particles, weights):
    # вибір 30% найкращих частинок
    idx = np.argsort(weights)[-int(0.3 * len(weights)):]
    selected = particles[idx]

    x_min = int(np.min(selected[:, 0]))
    x_max = int(np.max(selected[:, 0]))
    y_min = int(np.min(selected[:, 1]))
    y_max = int(np.max(selected[:, 1]))

    return x_min, y_min, x_max, y_max


frame_count = 0

# ГОЛОВНИЙ ЦИКЛ
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))
    frame_count += 1

    # DETECTION (фон)
    fg_mask = bg_subtractor.apply(frame)

    # морфологічна обробка
    kernel = np.ones((5, 5), np.uint8)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)      
    fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)        # дилатація для заповнення розривів      

    contours, _ = cv2.findContours(
        fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE   
    )

    measurement = None

    if contours:
        largest = max(contours, key=cv2.contourArea)

        if cv2.contourArea(largest) > 800:
            x, y, w_box, h_box = cv2.boundingRect(largest)           
            cx = x + w_box // 2
            cy = y + h_box // 2

            measurement = np.array([cx, cy])        
            cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)

    # PARTICLE FILTER
    particles = predict(particles)
    weights = update(particles, weights, measurement)

    Neff = 1. / np.sum(weights ** 2)     

    if Neff < N / 2:
        particles, weights = resample(particles, weights)

    state = estimate(particles, weights)
    x_est, y_est = int(state[0]), int(state[1])
  
    # ВІЗУАЛІЗАЦІЯ
    if frame_count > WARMUP:

        
        if measurement is not None:
            x_min, y_min, x_max, y_max = get_bbox(particles, weights)

            x_min = max(0, x_min-10)
            y_min = max(0, y_min-10)
            x_max = min(w, x_max+10)
            y_max = min(h, y_max+10)

            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 255, 0), 2)

        for p in particles[:30]:
            x, y = int(p[0]), int(p[1])
            if 0 <= x < w and 0 <= y < h:
                cv2.circle(frame, (x, y), 1, (255, 0, 0), -1)

        cv2.circle(frame, (x_est, y_est), 6, (0, 0, 255), -1)

        trajectory.append((x_est, y_est))
        for i in range(1, len(trajectory)):
            cv2.line(frame, trajectory[i-1], trajectory[i], (0, 0, 255), 2)


    cv2.imshow("Tracking", frame)
    cv2.imshow("Mask", fg_mask)

    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()


