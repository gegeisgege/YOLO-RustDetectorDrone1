# 🚁 Drone Pipeline Visual Inspection System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![YOLOv11](https://img.shields.io/badge/YOLO-v11n-green.svg)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

**Real-time corrosion and third-party damage detection for pipeline infrastructure using YOLOv11n + GPS localization**

---

## 🎯 Project Overview

This system enables automated visual inspection of pipeline infrastructure using drone-mounted cameras with GPS integration. Developed as part of a thesis project at [Your University], it addresses critical challenges in pipeline maintenance for Indonesia's oil, gas, and maritime industries.

### Key Features

- ✅ **YOLOv11n Object Detection** - Lightweight model optimized for real-time inference
- ✅ **GPS Localization** - Automatic geotagging of detected defects
- ✅ **Multiple Export Formats** - JSON, CSV, KML, GeoJSON, HTML maps
- ✅ **Dual Deployment** - Laptop testing + Raspberry Pi production
- ✅ **Interactive Visualization** - Web maps with severity-based clustering
- ✅ **Maintenance Prioritization** - Automated severity classification

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TRAINING PHASE                        │
│  Google Colab (T4 GPU) → YOLOv11n → best.pt            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   TESTING PHASE                          │
│  Windows Laptop → Webcam + Simulated GPS                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  DEPLOYMENT PHASE                        │
│  Raspberry Pi → Camera + Real GPS → Pipeline Inspection │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/gegeisgege/YOLO-RustDetectorDrone1.git
cd YOLO-RustDetectorDrone1

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Training (Google Colab)

```python
# Upload train_colab.py to Google Colab
# Set Runtime → T4 GPU
# Run all cells
# Download best.pt when complete
```

### 3. Testing (Laptop)

```bash
# Place best.pt in models/ folder
python scripts/webcam_test_with_config.py

# Controls:
# [Q] Quit  [S] Save  [P] Stats  [SPACE] Pause
```

### 4. Results

Check `results/` folder for:
- 📄 `final_detections.json` - Complete detection data
- 📊 `final_detections.csv` - Spreadsheet format
- 🗺️ `final_detections.kml` - Google Earth file
- 🌐 `final_map.html` - Interactive web map

---

## 📁 Project Structure

```
YOLO-RustDetectorDrone1/
├── docs/                    # Documentation
│   └── screenshots/         # Demo images
├── models/                  # Trained models
│   └── best.pt             # YOLOv11n weights
├── results/                 # Output files (gitignored)
├── scripts/                 # Source code
│   ├── config.py           # Configuration
│   ├── gps_integration_enhanced.py  # GPS module
│   └── webcam_test_with_config.py  # Main script
│   └── webcam.py
├── train_colab.py          # Colab training script
├── requirements.txt        # Dependencies
└── README.md              # This file
```

---

## ⚙️ Configuration

Edit `scripts/config.py` to customize:

```python
# Model settings
MODEL_PATH = 'models/best.pt'
CONFIDENCE_THRESHOLD = 0.25

# Webcam settings
CAMERA_INDEX = 0
WEBCAM_WIDTH = 1280
WEBCAM_HEIGHT = 720

# GPS simulation
GPS_START_LATITUDE = -7.2575   # Surabaya
GPS_START_LONGITUDE = 112.7521
```

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Model Size | ~6MB |
| Inference Speed | 50-100 FPS (GPU) / 15-30 FPS (CPU) |
| mAP50 | 0.XX (update after training) |
| Precision | 0.XX |
| Recall | 0.XX |

---

## 🎓 Academic Context

**Thesis:** Drone-Assisted Pipeline Inspection Using Computer Vision  
**Institution:** ITS, Surabaya
**Author:** Kris  
**Year:** 2024-2025  

**Keywords:** Computer Vision, YOLOv11, Pipeline Inspection, Corrosion Detection, GPS Localization, Drone Automation

---

## 📸 Screenshots

### Detection Demo
![Webcam Testing](docs/screenshots/detection_demo.png)

### Interactive Map
![GPS Map](docs/screenshots/interactive_map.png)

### Google Earth
![KML](docs/screenshots/google_earth.png)

---

## 🔧 Troubleshooting

### Webcam not opening
```python
# Try different camera indices in config.py
CAMERA_INDEX = 0  # Try 0, 1, 2...
```

### Low FPS
```python
# Reduce resolution
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480

# Skip frames
FRAME_SKIP = 2
```

### No detections
```python
# Lower confidence threshold
CONFIDENCE_THRESHOLD = 0.15
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 📞 Contact

**Kris**  
📧 [Your Email]  
🔗 [LinkedIn](your-linkedin)  
🎓 [University Profile](your-profile)

---

## 🙏 Acknowledgments

- Ultralytics for YOLOv11
- Roboflow for dataset management
- Google Colab for free GPU access
- [Your Advisors/Supervisors]

---

## ⭐ Star History

If this project helps your research, please consider giving it a star!

[![Star History](https://api.star-history.com/svg?repos=gegeisgege/YOLO-RustDetectorDrone1&type=Date)](https://star-history.com/#gegeisgege/YOLO-RustDetectorDrone1&Date)

---

**Last Updated:** April 2026


abstract

Abstract
Pipeline infrastructures are essential for supporting Indonesia’s oil, gas, and maritime
industries, yet their reliability is continually threatened by corrosion and third-party damage
(TPD). Manual inspection methods currently the dominant practice are time-consuming,
hazardous, and prone to human error, resulting in early-stage defects often being overlooked.
These limitations highlight the need for a more efficient, objective, and technologically
advanced inspection system. This research proposes the implementation of a drone-assisted
visual inspection framework integrating YOLOv12n lightweight object detection, TensorFlow,
and GPS-based localization to identify corrosion and TPD on surface pipelines in real time.
The study focuses on detecting visible surface anomalies for mechanical impacts or
Third Parties Damages that commonly occur in industrial and maritime environments. A dataset
consisting of field-acquired images and publicly available corrosion imagery is prepared
through preprocessing and augmentation before being annotated for YOLO training. The
YOLOv12n model is then trained and evaluated using performance metrics including precision,
recall, F1-score, mAP, and inference time. GPS coordinates are integrated to geotag detected
defects, enabling spatial mapping for maintenance planning.
The expected results of this research include achieving an accurate and computationally
efficient detection model suitable for deployment on drone platforms, improving inspection
coverage while reducing reliance on manual methods. The system aims to provide real-time,
location-aware defect identification, supporting predictive maintenance and enhancing the
safety and sustainability of Indonesia’s pipeline operations. This study contributes to the digital
transformation of industrial inspection practices and aligns with national efforts toward
infrastructure innovation and environmental protection.
Keywords: Computer Vision, Pipeline Inspection, YOLOv11n, Third-Party Damage,
Corrosion, GPS Localization.