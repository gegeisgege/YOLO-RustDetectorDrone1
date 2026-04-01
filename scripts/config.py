# ============================================================================
# CONFIGURATION FILE FOR PIPELINE INSPECTION SYSTEM
# ============================================================================

"""
Configuration for Drone Pipeline Visual Inspection System
Edit these settings - no need to modify main scripts
"""

# ============================================================================
# MODEL SETTINGS
# ============================================================================

MODEL_PATH = 'models/best.pt'  # Path to trained YOLOv11n model
CONFIDENCE_THRESHOLD = 0.25     # Detection confidence (0.0-1.0)

# ============================================================================
# WEBCAM SETTINGS
# ============================================================================

CAMERA_INDEX = 0           # Camera device (0=default, 1=external)
WEBCAM_WIDTH = 1280        # Resolution width
WEBCAM_HEIGHT = 720        # Resolution height

# ============================================================================
# GPS SIMULATION (for laptop testing)
# ============================================================================

GPS_START_LATITUDE = -7.2575   # Surabaya, Indonesia
GPS_START_LONGITUDE = 112.7521
FLIGHT_DISTANCE_KM = 0.5       # Simulated flight distance
GPS_POINTS_COUNT = 1000        # Number of GPS waypoints

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

OUTPUT_DIRECTORY = 'results'
AUTO_SAVE_INTERVAL = 10        # Save every N detections (0=disable)

# ============================================================================
# DISPLAY SETTINGS
# ============================================================================

SHOW_FPS = True
SHOW_GPS = True
SHOW_DETECTION_COUNT = True

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

FRAME_SKIP = 1                 # Process every Nth frame (1=all frames)
USE_GPU = False                # Set True if NVIDIA GPU available
MAX_FPS = 0                    # FPS limit (0=unlimited)

# ============================================================================
# EXPORT FORMATS
# ============================================================================

EXPORT_JSON = True
EXPORT_CSV = True
EXPORT_KML = True
EXPORT_GEOJSON = True
EXPORT_HTML_MAP = True

# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

VERBOSE = False                # Print detailed logs
SAVE_FRAMES = False           # Save detection images
FRAME_SAVE_DIR = 'results/frames'

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration values"""
    errors = []
    
    if not (0.0 <= CONFIDENCE_THRESHOLD <= 1.0):
        errors.append("CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
    if FRAME_SKIP < 1:
        errors.append("FRAME_SKIP must be >= 1")
    if AUTO_SAVE_INTERVAL < 0:
        errors.append("AUTO_SAVE_INTERVAL must be >= 0")
    if not (1.0 <= CLAHE_CLIP_LIMIT <= 8.0):
        errors.append("CLAHE_CLIP_LIMIT should be between 1.0 and 8.0")
    if not (1.0 <= SATURATION_SCALE <= 2.5):
        errors.append("SATURATION_SCALE should be between 1.0 and 2.5")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

# ============================================================================
# CAMERA COLOR & IMAGE ENHANCEMENT SETTINGS
# ============================================================================

# Force color mode — fixes B&W feed on some cameras/drivers
FORCE_COLOR = True             # Always convert frame to BGR color

# Corrosion-optimized image enhancement
ENHANCE_IMAGE = True           # Enable preprocessing before YOLO inference
CLAHE_CLIP_LIMIT = 2.5        # Contrast boost (1.0=none, 3.0=strong). 2.5 is best for rust
CLAHE_TILE_SIZE = 8           # CLAHE tile grid size (8x8 is standard)
SATURATION_SCALE = 1.4        # Boost color saturation (1.0=none, 1.4 boosts reds/oranges)
BRIGHTNESS_ALPHA = 1.05       # Slight brightness lift (1.0=none, keeps shadows visible)
BRIGHTNESS_BETA = 5           # Additive brightness offset (0=none)