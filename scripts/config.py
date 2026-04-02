# ============================================================================
# DRONE PIPELINE VISUAL INSPECTION SYSTEM - CONFIGURATION
# ============================================================================

"""
Configuration for Drone Pipeline Visual Inspection System
Edit these settings - no need to modify main scripts
"""

# ============================================================================
# MODEL SETTINGS
# ============================================================================

MODEL_PATH = 'models/best.pt'
CONFIDENCE_THRESHOLD = 0.25

# ============================================================================
# CAMERA SETTINGS
# ============================================================================

CAMERA_INDEX = 0
WEBCAM_WIDTH = 1280
WEBCAM_HEIGHT = 720
FORCE_COLOR = True              # Ensure BGR color output

# ============================================================================
# IMAGE ENHANCEMENT (Optimized for clarity without over-saturation)
# ============================================================================

ENHANCE_IMAGE = True
CLAHE_CLIP_LIMIT = 1.8          # Gentle contrast boost (was 2.5)
CLAHE_TILE_SIZE = 8
SATURATION_SCALE = 1.15         # Subtle color enhancement (was 1.4)
BRIGHTNESS_ALPHA = 1.02         # Minimal brightness adjustment (was 1.05)
BRIGHTNESS_BETA = 3             # Small additive offset (was 5)

# ============================================================================
# GPS SIMULATION
# ============================================================================

GPS_START_LATITUDE = -7.2575    # Surabaya, Indonesia
GPS_START_LONGITUDE = 112.7521
FLIGHT_DISTANCE_KM = 0.5
GPS_POINTS_COUNT = 1000

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

OUTPUT_DIRECTORY = 'results'
AUTO_SAVE_INTERVAL = 10         # Save every N detections (0=disable)
SAVE_FRAMES = False
FRAME_SAVE_DIR = 'results/frames'

# ============================================================================
# EXPORT FORMATS
# ============================================================================

EXPORT_JSON = True
EXPORT_CSV = True
EXPORT_KML = True
EXPORT_GEOJSON = True
EXPORT_HTML_MAP = True

# ============================================================================
# DISPLAY OPTIONS
# ============================================================================

SHOW_FPS = True
SHOW_GPS = True
SHOW_DETECTION_COUNT = True

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

FRAME_SKIP = 1                  # Process every Nth frame (1=all frames)
USE_GPU = False
MAX_FPS = 0                     # FPS limit (0=unlimited)
VERBOSE = False

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration values"""
    errors = []
    
    if not 0.0 <= CONFIDENCE_THRESHOLD <= 1.0:
        errors.append("CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
    if FRAME_SKIP < 1:
        errors.append("FRAME_SKIP must be >= 1")
    if AUTO_SAVE_INTERVAL < 0:
        errors.append("AUTO_SAVE_INTERVAL must be >= 0")
    if not 1.0 <= CLAHE_CLIP_LIMIT <= 8.0:
        errors.append("CLAHE_CLIP_LIMIT should be between 1.0 and 8.0")
    if not 1.0 <= SATURATION_SCALE <= 2.5:
        errors.append("SATURATION_SCALE should be between 1.0 and 2.5")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))