# 🍓 Raspberry Pi 4 Deployment Guide

## Hardware Requirements

- **Raspberry Pi 4** (2GB/4GB/8GB RAM recommended)
- **Camera**: Pi Camera Module v2/v3 OR USB webcam
- **GPS Module**: USB GPS (e.g., BU-353S4) OR UART GPS module
- **Storage**: 32GB+ microSD card (Class 10 or better)
- **Power**: 5V 3A USB-C power supply
- **Optional**: Cooling fan/heatsink for sustained operation

---

## Installation Steps

### 1. Prepare Raspberry Pi OS

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3-pip python3-venv
sudo apt-get install -y libopencv-dev python3-opencv
sudo apt-get install -y libatlas-base-dev libhdf5-dev
```

### 2. Install GPS Daemon

```bash
# Install gpsd
sudo apt-get install -y gpsd gpsd-clients python3-gpsd

# Configure gpsd
sudo nano /etc/default/gpsd

# Add these lines:
# START_DAEMON="true"
# GPSD_OPTIONS="-n"
# DEVICES="/dev/ttyUSB0"  # Change to your GPS device
# USBAUTO="true"

# Start gpsd service
sudo systemctl enable gpsd
sudo systemctl start gpsd

# Test GPS (wait 30-60 seconds for fix)
cgps -s
```

### 3. Setup Project

```bash
# Clone repository
cd ~
git clone https://github.com/gegeisgege/YOLO-RustDetectorDrone1.git
cd YOLO-RustDetectorDrone1

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements_raspi.txt

# For Pi Camera support (if using Pi Camera)
sudo apt-get install -y python3-picamera2
```

### 4. Transfer Trained Model

```bash
# From your laptop, transfer best.pt to Raspberry Pi:
scp models/best.pt pi@raspberrypi.local:~/YOLO-RustDetectorDrone1/models/

# OR use USB drive:
# 1. Copy best.pt to USB drive
# 2. Insert USB to Raspberry Pi
# 3. Copy: cp /media/pi/USB/best.pt ~/YOLO-RustDetectorDrone1/models/
```

---

## Configuration

Edit `scripts/config.py`:

```python
# Camera selection
CAMERA_INDEX = 0  # For USB camera (try 0, 1, 2 if not working)
# For Pi Camera, the script auto-detects it

# GPS settings (if using real GPS, these are ignored)
# Keep for fallback if GPS fails

# Performance tuning for Raspberry Pi
WEBCAM_WIDTH = 640   # Lower resolution for better FPS
WEBCAM_HEIGHT = 480
FRAME_SKIP = 2       # Process every 2nd frame
CONFIDENCE_THRESHOLD = 0.30  # Slightly higher for less noise

# Image enhancement (adjust based on camera quality)
ENHANCE_IMAGE = True
CLAHE_CLIP_LIMIT = 1.8
SATURATION_SCALE = 1.15
```

---

## Running the Inspector

### Test Mode (with display)

```bash
cd ~/YOLO-RustDetectorDrone1/scripts
source ../.venv/bin/activate
python raspi_inspector.py
```

### Headless Mode (no display, for drone deployment)

```bash
# Disable display
export DISPLAY=""

# Run in background with logging
nohup python raspi_inspector.py > inspector.log 2>&1 &

# Check if running
ps aux | grep raspi_inspector

# Stop
pkill -f raspi_inspector
```

### Auto-start on Boot

```bash
# Create systemd service
sudo nano /etc/systemd/system/pipeline-inspector.service
```

Add:
```ini
[Unit]
Description=Pipeline Inspector
After=network.target gpsd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/YOLO-RustDetectorDrone1/scripts
Environment="PATH=/home/pi/YOLO-RustDetectorDrone1/.venv/bin"
ExecStart=/home/pi/YOLO-RustDetectorDrone1/.venv/bin/python raspi_inspector.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable pipeline-inspector
sudo systemctl start pipeline-inspector

# Check status
sudo systemctl status pipeline-inspector

# View logs
sudo journalctl -u pipeline-inspector -f
```

---

## Camera Setup

### Pi Camera Module

```bash
# Enable camera interface
sudo raspi-config
# Select: Interface Options > Camera > Enable

# Reboot
sudo reboot

# Test camera
libcamera-hello
```

### USB Camera

```bash
# List cameras
v4l2-ctl --list-devices

# Test camera
ffplay /dev/video0
```

---

## GPS Setup

### Find GPS Device

```bash
# List USB devices
lsusb

# Check serial devices
ls /dev/tty*

# Common GPS devices:
# /dev/ttyUSB0 - USB GPS
# /dev/ttyAMA0 - UART GPS
```

### Test GPS

```bash
# Check GPS data stream
sudo cat /dev/ttyUSB0

# Use gpsd monitor
cgps -s

# Python test
python3 -c "import gpsd; gpsd.connect(); print(gpsd.get_current())"
```

---

## Performance Optimization

### 1. Reduce Resolution
```python
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
```

### 2. Frame Skipping
```python
FRAME_SKIP = 2  # Process every 2nd frame
```

### 3. Disable Display
```bash
export DISPLAY=""  # Run headless
```

### 4. Overclock (optional, requires cooling)
```bash
sudo nano /boot/config.txt

# Add:
# over_voltage=2
# arm_freq=1750
```

### 5. Disable Desktop
```bash
sudo systemctl set-default multi-user.target
```

---

## Troubleshooting

### Low FPS
- Reduce resolution to 640x480
- Increase FRAME_SKIP to 3 or 4
- Disable image enhancement
- Close other applications

### GPS Not Working
```bash
# Check gpsd status
sudo systemctl status gpsd

# Restart gpsd
sudo systemctl restart gpsd

# Check device permissions
sudo chmod 666 /dev/ttyUSB0
```

### Camera Not Detected
```bash
# For Pi Camera
vcgencmd get_camera

# For USB camera
v4l2-ctl --list-devices

# Try different CAMERA_INDEX (0, 1, 2)
```

### Out of Memory
```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set: CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## Data Retrieval

### Via SSH
```bash
# From laptop
scp pi@raspberrypi.local:~/YOLO-RustDetectorDrone1/results/* ./downloads/
```

### Via USB Drive
```bash
# On Raspberry Pi
cp -r results/ /media/pi/USB/
```

### Via Web Server (optional)
```bash
# Install nginx
sudo apt-get install nginx

# Copy results
sudo cp -r results /var/www/html/

# Access from laptop: http://raspberrypi.local/results/
```

---

## Monitoring

### Resource Usage
```bash
# CPU/Memory
htop

# Temperature
vcgencmd measure_temp

# Disk space
df -h
```

### Live Logs
```bash
# Inspector logs
tail -f inspector.log

# System logs
sudo journalctl -u pipeline-inspector -f
```

---

## Expected Performance

| Metric | Value |
|--------|-------|
| FPS (640x480) | 10-20 FPS |
| FPS (1280x720) | 5-10 FPS |
| GPS Fix Time | 30-60 seconds |
| Power Draw | 5-10W |
| Operating Temp | 40-60°C (with fan) |

---

## Safety Checklist

- [ ] Secure mounting on drone
- [ ] Waterproof housing if needed
- [ ] Stable power supply (battery)
- [ ] GPS antenna clear view of sky
- [ ] Camera lens protected
- [ ] Sufficient cooling
- [ ] Data backup enabled
- [ ] Emergency shutdown accessible

---

## Next Steps

1. Test indoor with USB GPS simulation
2. Test outdoor with real GPS fix
3. Mount on test platform
4. Field test in safe area
5. Full pipeline inspection deployment

---

**Last Updated:** April 2026