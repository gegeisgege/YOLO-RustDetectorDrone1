#!/usr/bin/env python3
"""
RASPBERRY PI 4 DEPLOYMENT SCRIPT
Project: Drone Pipeline Visual Inspection with YOLOv11n
Author: gege (Gerald Pillian)

Optimized for:
- Raspberry Pi 4 (2GB/4GB/8GB RAM)
- Pi Camera Module v2/v3 or USB camera
- Real GPS module (USB/UART)
- ARM CPU inference
"""

import cv2
import numpy as np
import os
import sys
import time
from datetime import datetime
from pathlib import Path

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
    print("❌ config.py not found!")
    sys.exit(1)

# Import GPS module
try:
    from gps_integration_enhanced import GPSTaggedDetection
    print("✅ GPS module loaded")
except ImportError:
    print("❌ gps_integration_enhanced.py not found!")
    sys.exit(1)

# GPS hardware integration
try:
    import gpsd
    GPS_AVAILABLE = True
    print("✅ gpsd library found")
except ImportError:
    GPS_AVAILABLE = False
    print("⚠️ gpsd not installed - GPS disabled")
    print("   Install: sudo apt-get install gpsd gpsd-clients python3-gpsd")


class RaspberryPiInspector:
    """Raspberry Pi optimized pipeline inspector with real GPS"""

    def __init__(self):
        """Initialize with hardware optimizations"""
        print("🚀 Initializing Raspberry Pi Inspector...")
        print(f"   Model: {MODEL_PATH}")
        print(f"   Confidence: {CONFIDENCE_THRESHOLD}")

        # Check model exists
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"\n❌ Model not found: {MODEL_PATH}\n"
                f"Transfer best.pt to Raspberry Pi models/ folder"
            )

        # Load YOLO with CPU optimization
        self.model = YOLO(MODEL_PATH)
        self.model.to('cpu')  # Force CPU on Raspberry Pi
        print("   Device: ARM CPU")

        # Initialize GPS handler
        self.gps_handler = GPSTaggedDetection()
        self.gps_connected = False
        
        if GPS_AVAILABLE:
            self._init_gps()
        else:
            print("   GPS: Disabled (gpsd not available)")

        # Stats
        self.frame_count = 0
        self.detection_count = 0
        self.fps_history = []
        self.start_time = time.time()

        # Create output directory
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        
        print("✅ Initialization complete!\n")

    def _init_gps(self):
        """Initialize GPS connection"""
        try:
            gpsd.connect()
            
            # Wait for GPS fix
            print("   GPS: Waiting for fix...", end='', flush=True)
            timeout = 30
            start = time.time()
            
            while time.time() - start < timeout:
                packet = gpsd.get_current()
                if packet.mode >= 2:  # 2D or 3D fix
                    self.gps_connected = True
                    print(" ✅ Fixed")
                    print(f"   Position: {packet.lat:.6f}, {packet.lon:.6f}")
                    return
                time.sleep(0.5)
                print(".", end='', flush=True)
            
            print(" ⚠️ Timeout")
            print("   GPS: Running without fix")
            
        except Exception as e:
            print(f"\n   GPS Error: {e}")
            print("   GPS: Disabled")
            self.gps_connected = False

    def _get_gps_position(self):
        """Get current GPS coordinates"""
        if not GPS_AVAILABLE or not self.gps_connected:
            return 0.0, 0.0, 0.0
        
        try:
            packet = gpsd.get_current()
            
            if packet.mode >= 2:
                lat = packet.lat
                lon = packet.lon
                alt = packet.alt if hasattr(packet, 'alt') else 0.0
                return lat, lon, alt
            else:
                return 0.0, 0.0, 0.0
                
        except Exception as e:
            if VERBOSE:
                print(f"⚠️ GPS read error: {e}")
            return 0.0, 0.0, 0.0

    def _preprocess_frame(self, frame):
        """Optimized preprocessing for Raspberry Pi"""
        if not ENHANCE_IMAGE:
            return frame

        # Force color mode
        if FORCE_COLOR and len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # CLAHE on luminance only (LAB colorspace)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=(CLAHE_TILE_SIZE, CLAHE_TILE_SIZE)
        )
        l = clahe.apply(l)
        
        lab = cv2.merge([l, a, b])
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Boost saturation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * SATURATION_SCALE, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Brightness adjustment
        frame = cv2.convertScaleAbs(frame, alpha=BRIGHTNESS_ALPHA, beta=BRIGHTNESS_BETA)

        return frame

    def process_frame(self, frame):
        """Process single frame with GPS tagging"""
        # Get real GPS coordinates
        lat, lon, alt = self._get_gps_position()

        # Preprocess
        if ENHANCE_IMAGE:
            frame = self._preprocess_frame(frame)

        # YOLO inference
        start = time.time()
        results = self.model.predict(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
            imgsz=640,  # Fixed size for consistency
            device='cpu'
        )[0]
        inference_time = time.time() - start

        # Calculate FPS
        fps = 1.0 / inference_time if inference_time > 0 else 0
        self.fps_history.append(fps)
        if len(self.fps_history) > 30:
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
        """Draw info overlay optimized for small screens"""
        h, w = frame.shape[:2]

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 110), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Info text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "RASPI INSPECTOR - LIVE",
                   (10, 25), font, 0.6, (0, 255, 255), 2)

        if SHOW_GPS:
            gps_status = "FIXED" if self.gps_connected else "NO FIX"
            gps_color = (0, 255, 0) if self.gps_connected else (0, 165, 255)
            cv2.putText(frame, f"GPS: {lat:.6f}, {lon:.6f} [{gps_status}]",
                       (10, 50), font, 0.4, gps_color, 1)

        # Stats
        stats = []
        if SHOW_FPS:
            avg_fps = np.mean(self.fps_history) if self.fps_history else 0
            stats.append(f"FPS: {avg_fps:.1f}")
        if SHOW_DETECTION_COUNT:
            stats.append(f"Det: {self.detection_count}")
        stats.append(f"Frame: {self.frame_count}")

        cv2.putText(frame, " | ".join(stats),
                   (10, 75), font, 0.4, (255, 255, 255), 1)

        # Runtime
        runtime = time.time() - self.start_time
        cv2.putText(frame, f"Runtime: {int(runtime//60)}:{int(runtime%60):02d}",
                   (10, 100), font, 0.4, (255, 255, 0), 1)

        # Detection indicator
        if num_dets > 0:
            cv2.circle(frame, (w - 25, 25), 12, (0, 0, 255), -1)
            cv2.putText(frame, str(num_dets), (w - 32, 30),
                       font, 0.5, (255, 255, 255), 2)

    def _init_camera(self):
        """Initialize camera with Raspberry Pi optimizations"""
        print("📷 Initializing camera...")
        
        # Try Pi Camera first
        try:
            from picamera2 import Picamera2
            print("   Trying Pi Camera...")
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"size": (WEBCAM_WIDTH, WEBCAM_HEIGHT)}
            )
            picam2.configure(config)
            picam2.start()
            print("   ✅ Pi Camera initialized")
            return picam2, "picamera"
        except Exception as e:
            if VERBOSE:
                print(f"   Pi Camera failed: {e}")

        # Fallback to USB camera
        print("   Trying USB camera...")
        cap = cv2.VideoCapture(CAMERA_INDEX)
        
        if not cap.isOpened():
            raise RuntimeError("❌ No camera found!")

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("   ✅ USB camera initialized")
        return cap, "usb"

    def run(self):
        """Main execution loop - Raspberry Pi optimized"""
        print("="*70)
        print("🚁 RASPBERRY PI PIPELINE INSPECTOR - LIVE MODE")
        print("="*70)
        print(f"Output: {OUTPUT_DIRECTORY}")
        print(f"GPS: {'Enabled' if self.gps_connected else 'Disabled'}")
        print(f"Auto-save: Every {AUTO_SAVE_INTERVAL} detections" if AUTO_SAVE_INTERVAL > 0 else "Auto-save: Disabled")
        print("\nControls:")
        print("  [Q] Quit  [S] Save  [P] Stats  [R] Reset")
        print("="*70 + "\n")

        # Initialize camera
        try:
            camera, cam_type = self._init_camera()
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return

        last_save = 0
        frame_counter = 0

        try:
            while True:
                # Read frame
                if cam_type == "picamera":
                    frame = camera.capture_array()
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    ret, frame = camera.read()
                    if not ret:
                        print("⚠️ Frame read failed")
                        break

                # Frame skipping
                frame_counter += 1
                if frame_counter % FRAME_SKIP != 0:
                    continue

                # Process
                annotated = self.process_frame(frame)

                # Auto-save
                if AUTO_SAVE_INTERVAL > 0 and self.detection_count > 0:
                    if self.detection_count >= last_save + AUTO_SAVE_INTERVAL:
                        self._save_results(auto=True)
                        last_save = self.detection_count

                # Display (optional - comment out for headless operation)
                if os.environ.get('DISPLAY'):
                    cv2.imshow('Pipeline Inspector', annotated)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s'):
                        self._save_results()
                    elif key == ord('p'):
                        self.gps_handler.print_summary_report()
                    elif key == ord('r'):
                        self._reset()

                # Save frames if enabled
                if SAVE_FRAMES and self.detection_count > 0:
                    self._save_detection_frame(annotated)

        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")

        finally:
            # Cleanup
            if cam_type == "picamera":
                camera.stop()
            else:
                camera.release()
            
            cv2.destroyAllWindows()
            self._save_results(final=True)
            self._print_stats()

    def _save_detection_frame(self, frame):
        """Save detection frame to disk"""
        if not os.path.exists(FRAME_SAVE_DIR):
            os.makedirs(FRAME_SAVE_DIR)
        
        filename = f"{FRAME_SAVE_DIR}/detection_{self.detection_count:06d}.jpg"
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

    def _save_results(self, auto=False, final=False):
        """Save results in configured formats"""
        prefix = "final_" if final else ""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            if EXPORT_JSON:
                self.gps_handler.save_to_json(
                    f'{OUTPUT_DIRECTORY}/{prefix}detections_{timestamp}.json'
                )
            if EXPORT_CSV:
                self.gps_handler.save_to_csv(
                    f'{OUTPUT_DIRECTORY}/{prefix}detections_{timestamp}.csv'
                )
            if EXPORT_KML:
                self.gps_handler.save_to_kml(
                    f'{OUTPUT_DIRECTORY}/{prefix}detections_{timestamp}.kml'
                )
            if EXPORT_GEOJSON:
                self.gps_handler.save_to_geojson(
                    f'{OUTPUT_DIRECTORY}/{prefix}detections_{timestamp}.geojson'
                )
            if EXPORT_HTML_MAP:
                self.gps_handler.create_interactive_map(
                    f'{OUTPUT_DIRECTORY}/{prefix}map_{timestamp}.html'
                )

            status = "Auto-saved" if auto else "Saved"
            print(f"💾 {status}: {self.detection_count} detections ({timestamp})")
        except Exception as e:
            print(f"⚠️ Save error: {e}")

    def _reset(self):
        """Reset detection counter"""
        self.detection_count = 0
        self.gps_handler = GPSTaggedDetection()
        print("🔄 Reset complete")

    def _print_stats(self):
        """Print final statistics"""
        runtime = time.time() - self.start_time
        
        print("\n" + "="*70)
        print("📊 SESSION STATISTICS")
        print("="*70)
        print(f"Runtime: {int(runtime//60)}m {int(runtime%60)}s")
        print(f"Frames: {self.frame_count}")
        print(f"Detections: {self.detection_count}")
        if self.fps_history:
            print(f"Avg FPS: {np.mean(self.fps_history):.1f}")
        if self.detection_count > 0:
            print(f"Detection rate: {self.detection_count/self.frame_count*100:.2f}%")
        print("="*70 + "\n")

        self.gps_handler.print_summary_report()
        print(f"\n📁 Results: {os.path.abspath(OUTPUT_DIRECTORY)}/")


def main():
    """Entry point"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║         🍓 RASPBERRY PI PIPELINE INSPECTOR                     ║
    ║              YOLOv11n + Real GPS                               ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    # Check if running on Raspberry Pi
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' not in model:
                print("⚠️ Warning: Not running on Raspberry Pi")
    except:
        print("⚠️ Warning: Cannot detect hardware")

    try:
        inspector = RaspberryPiInspector()
        inspector.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()