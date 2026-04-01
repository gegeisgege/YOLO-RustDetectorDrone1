#!/usr/bin/env python3
"""
OPTIMIZED WEBCAM TESTING SCRIPT
Project: Drone Pipeline Visual Inspection with YOLOv11n
Author: Kris
"""

import cv2
import numpy as np
import os
import sys
from datetime import datetime

# Import YOLO
try:
    from ultralytics import YOLO
except ImportError:
    print("❌ ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)

# Import config
try:
    from config import *
    print("✅ Configuration loaded")
except ImportError:
    print("❌ config.py not found in current directory!")
    sys.exit(1)

# Import GPS module
try:
    from gps_integration_enhanced import GPSTaggedDetection, simulate_gps_for_webcam
    print("✅ GPS module loaded")
except ImportError:
    print("❌ gps_integration_enhanced.py not found!")
    sys.exit(1)


class WebcamInspector:
    """Optimized webcam pipeline inspector"""

    def __init__(self):
        """Initialize with config validation"""
        print("🚀 Initializing Inspector...")
        print(f"   Model: {MODEL_PATH}")
        print(f"   Confidence: {CONFIDENCE_THRESHOLD}")

        # Check model exists
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"\n❌ Model not found: {MODEL_PATH}\n"
                f"Download best.pt from Colab and place in models/ folder"
            )

        # Load YOLO model
        self.model = YOLO(MODEL_PATH)

        # Check if GPU available
        self.device = 'cuda' if USE_GPU and self._check_gpu() else 'cpu'
        print(f"   Device: {self.device.upper()}")

        # Initialize GPS
        self.gps_handler = GPSTaggedDetection()
        self.gps_points = simulate_gps_for_webcam(
            num_frames=GPS_POINTS_COUNT,
            start_lat=GPS_START_LATITUDE,
            start_lon=GPS_START_LONGITUDE,
            flight_distance_km=FLIGHT_DISTANCE_KM
        )
        self.gps_index = 0

        # Stats
        self.frame_count = 0
        self.detection_count = 0
        self.fps_history = []

        print("✅ Initialization complete!\n")

    def _check_gpu(self):
        """Check CUDA availability"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    def _preprocess_frame(self, frame):
        """
        Fix B&W feed and enhance color for better corrosion detection.
        Corrosion = orange/red/brown — these colors must be preserved and boosted.
        """
        # --- Fix 1: Force color ---
        # If camera driver returned greyscale (2D array or 3-channel grey), convert it
        if FORCE_COLOR:
            if len(frame.shape) == 2:
                # True greyscale array — expand to 3 channels
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 3:
                b, g, r = cv2.split(frame)
                if np.array_equal(b, g) and np.array_equal(g, r):
                    # Camera is sending grey packed as BGR.
                    # Decode it as a proper greyscale image then re-encode as BGR.
                    # This does NOT add color that isn't there — but it ensures
                    # the pipeline treats it as color so CLAHE/saturation still run.
                    grey = b  # all 3 channels identical, just take one
                    frame = cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)

        # --- Fix 2: CLAHE contrast enhancement on luminance only ---
        # Work in LAB so we only boost luminance, not hue — keeps rust colors accurate
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=(CLAHE_TILE_SIZE, CLAHE_TILE_SIZE)
        )
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # --- Fix 3: Boost saturation to make rust orange/red stand out ---
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * SATURATION_SCALE, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # --- Fix 4: Mild brightness/contrast lift ---
        frame = cv2.convertScaleAbs(frame, alpha=BRIGHTNESS_ALPHA, beta=BRIGHTNESS_BETA)

        return frame

    def process_frame(self, frame):
        """Process single frame - OPTIMIZED"""
        # Get GPS
        lat, lon, alt = self.gps_points[self.gps_index % len(self.gps_points)]
        self.gps_index += 1

        # Preprocess: fix color + enhance for corrosion detection
        frame = self._preprocess_frame(frame)

        # YOLO inference
        start = cv2.getTickCount()
        results = self.model.predict(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
            device=self.device
        )[0]
        end = cv2.getTickCount()

        # Calculate FPS
        fps = cv2.getTickFrequency() / (end - start)
        self.fps_history.append(fps)
        if len(self.fps_history) > 30:  # Keep last 30 frames
            self.fps_history.pop(0)

        # Process detections
        for box in results.boxes:
            self.gps_handler.add_detection(
                image_name=f"frame_{self.frame_count:06d}.jpg",
                class_name=results.names[int(box.cls[0])],
                confidence=float(box.conf[0]),
                bbox=box.xyxy[0].cpu().numpy().tolist(),
                latitude=lat,
                longitude=lon,
                altitude=alt
            )
            self.detection_count += 1

        # Draw annotations
        annotated = results.plot()
        self._draw_overlay(annotated, lat, lon, alt, fps, len(results.boxes))

        self.frame_count += 1
        return annotated

    def _draw_overlay(self, frame, lat, lon, alt, fps, num_dets):
        """Draw optimized info overlay"""
        h, w = frame.shape[:2]

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Info text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "PIPELINE INSPECTION - TESTING MODE",
                   (10, 30), font, 0.7, (0, 255, 255), 2)

        if SHOW_GPS:
            cv2.putText(frame, f"GPS: {lat:.6f}, {lon:.6f} | Alt: {alt:.1f}m",
                       (10, 60), font, 0.5, (0, 255, 0), 2)

        stats = []
        if SHOW_FPS:
            avg_fps = np.mean(self.fps_history) if self.fps_history else 0
            stats.append(f"FPS: {avg_fps:.1f}")
        if SHOW_DETECTION_COUNT:
            stats.append(f"Detections: {self.detection_count}")
        stats.append(f"Frame: {self.frame_count}")

        cv2.putText(frame, " | ".join(stats),
                   (10, 90), font, 0.5, (255, 255, 255), 2)

        cv2.putText(frame, "MODE: SIMULATED GPS",
                   (10, 120), font, 0.5, (255, 255, 0), 2)

        # Detection indicator
        if num_dets > 0:
            cv2.circle(frame, (w - 30, 30), 15, (0, 0, 255), -1)
            cv2.putText(frame, str(num_dets), (w - 38, 37),
                       font, 0.6, (255, 255, 255), 2)

    def run(self):
        """Main execution loop - OPTIMIZED"""
        print("="*70)
        print("🎥 STARTING WEBCAM TESTING")
        print("="*70)
        print(f"Output: {OUTPUT_DIRECTORY}")
        print(f"Auto-save: Every {AUTO_SAVE_INTERVAL} detections" if AUTO_SAVE_INTERVAL > 0 else "Auto-save: Disabled")
        print("\nControls:")
        print("  [Q] Quit  [S] Save  [P] Stats  [R] Reset  [SPACE] Pause")
        print("="*70 + "\n")

        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

        # Open webcam — force color mode at backend level
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)  # CAP_DSHOW forces Windows color driver
        if not cap.isOpened():
            # Fallback to default backend
            cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            print(f"❌ Failed to open camera {CAMERA_INDEX}")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Force MJPG = color
        cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)

        print("✅ Webcam ready\n")

        paused = False
        last_save = 0
        frame_counter = 0
        annotated_frame = None

        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        print("⚠️ Frame read failed")
                        break

                    # Frame skipping
                    frame_counter += 1
                    if frame_counter % FRAME_SKIP != 0:
                        continue

                    # Process
                    annotated_frame = self.process_frame(frame)

                    # Auto-save
                    if AUTO_SAVE_INTERVAL > 0 and self.detection_count > 0:
                        if self.detection_count >= last_save + AUTO_SAVE_INTERVAL:
                            self._save_results(auto=True)
                            last_save = self.detection_count
                else:
                    if annotated_frame is not None:
                        cv2.putText(annotated_frame, "PAUSED",
                                   (annotated_frame.shape[1]//2 - 80, annotated_frame.shape[0]//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)

                if annotated_frame is not None:
                    cv2.imshow('Pipeline Inspection', annotated_frame)

                # Keyboard controls
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self._save_results()
                elif key == ord('p'):
                    self.gps_handler.print_summary_report()
                elif key == ord('r'):
                    self.detection_count = 0
                    self.gps_handler = GPSTaggedDetection()
                    print("🔄 Reset")
                elif key == ord(' '):
                    paused = not paused

        except KeyboardInterrupt:
            print("\n⚠️ Interrupted")

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self._save_results(final=True)
            self._print_stats()

    def _save_results(self, auto=False, final=False):
        """Save with configured formats"""
        prefix = "final_" if final else ""

        try:
            if EXPORT_JSON:
                self.gps_handler.save_to_json(f'{OUTPUT_DIRECTORY}/{prefix}detections.json')
            if EXPORT_CSV:
                self.gps_handler.save_to_csv(f'{OUTPUT_DIRECTORY}/{prefix}detections.csv')
            if EXPORT_KML:
                self.gps_handler.save_to_kml(f'{OUTPUT_DIRECTORY}/{prefix}detections.kml')
            if EXPORT_GEOJSON:
                self.gps_handler.save_to_geojson(f'{OUTPUT_DIRECTORY}/{prefix}detections.geojson')
            if EXPORT_HTML_MAP:
                self.gps_handler.create_interactive_map(f'{OUTPUT_DIRECTORY}/{prefix}map.html')

            status = "Auto-saved" if auto else "Saved"
            print(f"💾 {status}: {self.detection_count} detections")
        except Exception as e:
            print(f"⚠️ Save error: {e}")

    def _print_stats(self):
        """Print final statistics"""
        print("\n" + "="*70)
        print("📊 SESSION STATISTICS")
        print("="*70)
        print(f"Frames: {self.frame_count}")
        print(f"Detections: {self.detection_count}")
        if self.fps_history:
            print(f"Avg FPS: {np.mean(self.fps_history):.1f}")
        print("="*70 + "\n")

        self.gps_handler.print_summary_report()
        print(f"\n📁 Results: {os.path.abspath(OUTPUT_DIRECTORY)}/")


def main():
    """Entry point"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║        🚁 DRONE PIPELINE INSPECTION - TESTING SYSTEM           ║
    ║              YOLOv11n + GPS Localization                       ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    try:
        inspector = WebcamInspector()
        inspector.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()