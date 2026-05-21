# Incremental 3D Reconstruction using Structure from Motion

This project implements an incremental Structure from Motion (SfM) pipeline for 3D object reconstruction from multiple images using Python and OpenCV.

The program:
- detects and matches image features using SIFT,
- estimates camera motion,
- triangulates 3D points,
- incrementally reconstructs a sparse 3D scene,
- visualizes the reconstructed point cloud and mesh.

---

# Features

- SIFT feature detection and matching
- Essential matrix estimation
- Camera pose recovery
- Incremental PnP camera localization
- Linear triangulation
- Reprojection error analysis
- Colored point cloud generation
- 3D visualization with Open3D
- Mesh reconstruction using Alpha Shapes

---

# Project Structure

```text
Mincrem3D/
│
├── img/
│   └── dino/
│       ├── *.jpg / *.png / *.ppm
│
├── colors.py
├── config.py
├── features.py
├── triangulation.py
├── utils.py
├── visualization.py
├── main.py
├── requirements.txt
└── README.md
```

---

# Requirements

- Python 3.10+
- OpenCV
- NumPy
- Matplotlib
- Open3D

---

# Installation (PyCharm)

This project is intended to be run using PyCharm IDE.

---

## 1. Clone repository in PyCharm

1. Open **PyCharm**
2. Click **Get from VCS**
3. Paste repository URL:
   ```
   https://github.com/YOUR_USERNAME/Mincrem3D.git
   ```
4. Choose local folder
5. Click **Clone**

---

## 2. Create virtual environment (PyCharm)

1. Go to **File → Settings → Project → Python Interpreter**
2. Click **Add Interpreter**
3. Select **Virtualenv Environment**
4. Choose:
   - New environment
   - Location: `venv/`
   - Base interpreter: your Python version
5. Click **OK**

PyCharm will automatically create and activate the virtual environment.

---

## 3. Install dependencies (PyCharm)

1. Open `requirements.txt`
2. PyCharm will show a prompt:
   **Install requirements?**
3. Click **Install**

OR manually:
- Go to **Python Interpreter**
- Click **+**
- Search and install:
  - numpy
  - opencv-python
  - matplotlib
  - open3d

---

## 4. Run the project (PyCharm)

1. Open `main.py`
2. Right-click inside the file
3. Click **Run 'main'**

OR:
- Click green ▶ button in the top-right corner

---

# Requirements File

Make sure `requirements.txt` contains:

```text
numpy==2.2.5
opencv-python==4.11.0.86
matplotlib==3.10.1
open3d==0.19.0
```

---

# Notes

- No need to manually run `venv\Scripts\activate` in PyCharm
- No need to use terminal for installation
- PyCharm manages environment automatically

---

# How the Pipeline Works

## 1. Feature Detection
SIFT is used to detect keypoints and descriptors for every image.

## 2. Feature Matching
FLANN-based matcher performs nearest-neighbor matching between consecutive frames.

## 3. Initial Reconstruction
For the first image pair:
- the Essential matrix is estimated
- camera pose is recovered
- initial 3D points are triangulated

## 4. Incremental Reconstruction
For every next frame:
- camera pose is estimated using PnP
- new 3D points are triangulated
- reconstructed scene grows incrementally

## 5. Error Estimation
The reprojection error is computed for evaluating reconstruction quality.

## 6. Visualization
The program:
- builds a colored point cloud
- removes outliers
- reconstructs a mesh
- visualizes the result using Open3D

---

# Input Data

Place input images inside:

```text
img/dino/
```

Dataset:
https://www.robots.ox.ac.uk/~vgg/data/mview/
Supported formats:
- `.jpg`
- `.png`
- `.ppm`

---

# Camera Intrinsic Matrix

Camera calibration matrix is defined in `config.py`:

---

# Output

The program generates:
- sparse 3D point cloud
- reconstructed mesh
- reprojection error graph
- statistics of added 3D points

Saved file:

```text
reconstruction_stats.png
```

---

# Author

Roksolana Savuliak  
Applied Mathematics Student