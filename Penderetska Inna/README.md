# Drone Detection YOLOv8x — інструкція з запуску

1. Завантажте VS Code: [https://code.visualstudio.com/](https://code.visualstudio.com/)
2. Встановіть програму
3. Завантажте Python 3.11: [https://www.python.org/downloads/](https://www.python.org/downloads/)
3. Перевірте в терміналі PowerShell чи встановився Пайтон 
4. Розпакуйте папку `Drone-Detection-YOLOv8x` у VS Code: **File → Open Folder** і виберіть папку проєкту 
5. Створіть venv:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

Якщо PowerShell блокуватиме активацію то:

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1

6. Встановіть бібліотеки 
pip install torch torchvision
pip install ultralytics
pip install opencv-python
pip install numpy
pip install matplotlib
pip install pillow
pip install pyyaml
pip install pandas
pip install scipy
pip install tqdm
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ultralytics opencv-python numpy matplotlib pillow pyyaml pandas scipy tqdm
6. Запуск детекції на відео (основний сценарій)

Тестове відео за замовчуванням:

`test/pexels-joseph-redfield-8459631 (1080p).mp4`

python drone_detection_yolov8x.py 

**Запис результату у файл** (якщо вікно OpenCV не відкривається):

```powershell
python drone_detection_yolov8x.py --weights weights/best.pt --out-video "preview_out.mp4"
```
Параметри з якими можна запускати 
 `--conf 0.45` - поріг впевненості детекції 
  `--imgsz 320` - більше — точніше, повільніше
 `--device cpu` - примусово CPU 
 `--show-fps`- показати FPS на екрані 
 `--no-track` - predict без трекера 

python drone_trajectory_kalman.py -запуск Калмана 

8. Навчання моделі 
Потрібні папки датасету з `data.yaml`: `train/images`, `valid/images`, `test/images`.
python start_training.py
Результати з’являться у `runs/detect/`. Найкращі ваги — у `runs/detect/.../weights/best.pt`. Їх можна передати в `--weights` при детекції.

