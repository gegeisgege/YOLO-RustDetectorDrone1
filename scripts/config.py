# ============================================================================
# CONFIGURATION FILE FOR WEBCAM TESTING
# Edit these settings instead of modifying the main script
# ============================================================================

"""
Simple configuration - just change the values below!
"""

# ============================================================================
# MODEL SETTINGS
# ============================================================================

# Path to your trained YOLO model
# After training in Colab, download best.pt and place it in models/ folder
MODEL_PATH = 'models/best.pt'

# Detection confidence threshold (0.0 to 1.0)
# Lower = more detections (may include false positives)
# Higher = fewer detections (more accurate but might miss some)
CONFIDENCE_THRESHOLD = 0.25

# ============================================================================
# WEBCAM SETTINGS
# ============================================================================

# Camera index (usually 0 for built-in webcam)
# If webcam doesn't open, try: 0, 1, 2, etc.
CAMERA_INDEX = 0

# Webcam resolution
# Lower resolution = faster FPS, Higher resolution = better quality
WEBCAM_WIDTH = 1280
WEBCAM_HEIGHT = 720

# ============================================================================
# GPS SIMULATION SETTINGS
# ============================================================================

# Starting GPS coordinates (default: Surabaya, Indonesia)
GPS_START_LATITUDE = -7.2575
GPS_START_LONGITUDE = 112.7521

# Simulated flight distance in kilometers
FLIGHT_DISTANCE_KM = 0.5

# Number of GPS points to generate
GPS_POINTS_COUNT = 1000

# ============================================================================
# SAVING SETTINGS
# ============================================================================

# Directory to save results
OUTPUT_DIRECTORY = 'results'

# Auto-save interval (save results every N detections)
# Set to 0 to disable auto-save
AUTO_SAVE_INTERVAL = 10

# ============================================================================
# DISPLAY SETTINGS
# ============================================================================

# Show FPS in overlay
SHOW_FPS = True

# Show GPS coordinates in overlay
SHOW_GPS = True

# Show detection count in overlay
SHOW_DETECTION_COUNT = True

# ============================================================================
# ADVANCED SETTINGS (usually don't need to change)
# ============================================================================

# Maximum FPS (0 = unlimited)
MAX_FPS = 0

# Enable verbose logging
VERBOSE = True

# Save individual frames with detections
SAVE_FRAMES = False

# Frame save directory (if SAVE_FRAMES is True)
FRAME_SAVE_DIR = 'results/frames'

# ============================================================================
# EXPORT FORMATS
# ============================================================================

# Which formats to export (True/False for each)
EXPORT_JSON = True
EXPORT_CSV = True
EXPORT_KML = True
EXPORT_GEOJSON = True
EXPORT_HTML_MAP = True

# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================

# Skip frames for faster processing (1 = process every frame, 2 = every other frame)
FRAME_SKIP = 1

# Use GPU if available (requires CUDA-enabled PyTorch)
USE_GPU = False  # Set to True if you have NVIDIA GPU on laptop

# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
HOW TO USE THIS CONFIG:

1. Basic setup (most common):
   - Set MODEL_PATH to your trained model location
   - Adjust CONFIDENCE_THRESHOLD (start with 0.25)
   - Try different CAMERA_INDEX if webcam doesn't open

2. Performance issues (slow FPS):
   - Lower WEBCAM_WIDTH and WEBCAM_HEIGHT (try 640x480)
   - Increase FRAME_SKIP to 2 or 3
   - Increase CONFIDENCE_THRESHOLD to 0.5

3. Too few detections:
   - Lower CONFIDENCE_THRESHOLD to 0.15 or 0.20
   - Make sure you're showing rusty/corroded objects to camera

4. GPS location:
   - Change GPS_START_LATITUDE and GPS_START_LONGITUDE to your area
   - Adjust FLIGHT_DISTANCE_KM for wider/narrower coverage

5. Saving:
   - Change OUTPUT_DIRECTORY for different save location
   - Adjust AUTO_SAVE_INTERVAL (higher = save less often)
   - Enable SAVE_FRAMES to save images with detections

Then run:
    python webcam_test_with_config.py
"""