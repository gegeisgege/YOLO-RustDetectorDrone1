#!/usr/bin/env python3
"""
WEBCAM TESTING SCRIPT - CONFIG FILE VERSION
All settings can be changed in config.py without editing this file!

Author: Kris
Project: Drone Pipeline Visual Inspection with GPS
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os

# Import configuration
try:
    from scripts.config import *
    print("✅ Configuration loaded from config.py")
except ImportError:
    print("⚠️ config.py not found! Using default settings.")
    # Default settings if config.py is missing
    MODEL_PATH = 'models/best.pt'
    CONFIDENCE_THRESHOLD = 0.25
    CAMERA_INDEX = 0
    WEBCAM_WIDTH = 1280
    WEBCAM_HEIGHT = 720
    GPS_START_LATITUDE = -7.2575
    GPS_START_LONGITUDE = 112.7521
    FLIGHT_DISTANCE_KM = 0.5
    GPS_POINTS_COUNT = 1000
    OUTPUT_DIRECTORY = 'results'
    AUTO_SAVE_INTERVAL = 10
    SHOW_FPS = True
    SHOW_GPS = True
    SHOW_DETECTION_COUNT = True
    FRAME_SKIP = 1
    EXPORT_JSON = True
    EXPORT_CSV = True
    EXPORT_KML = True
    EXPORT_GEOJSON = True
    EXPORT_HTML_MAP = True

# Import GPS module
try:
    from gps_integration_enhanced import GPSTaggedDetection, simulate_gps_for_webcam
    print("✅ GPS integration module loaded")
except ImportError:
    print("⚠️ GPS module not found. Make sure gps_integration_enhanced.py is in the same folder!")
    exit(1)


class WebcamPipelineInspector:
    """Main class for webcam testing with config file support"""
    
    def __init__(self):
        """Initialize using settings from config.py"""
        print("🚀 Initializing Pipeline Inspector...")
        print(f"   Model: {MODEL_PATH}")
        print(f"   Confidence: {CONFIDENCE_THRESHOLD}")
        print(f"   Camera: {CAMERA_INDEX}")
        
        # Load YOLO model
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        
        self.model = YOLO(MODEL_PATH)
        
        # Initialize GPS handler
        self.gps_handler = GPSTaggedDetection()
        
        # Simulate GPS flight path
        print(f"🛰️ Generating {GPS_POINTS_COUNT} GPS points...")
        self.gps_points = simulate_gps_for_webcam(
            num_frames=GPS_POINTS_COUNT,
            start_lat=GPS_START_LATITUDE,
            start_lon=GPS_START_LONGITUDE,
            flight_distance_km=FLIGHT_DISTANCE_KM
        )
        self.gps_index = 0
        
        # Statistics
        self.frame_count = 0
        self.detection_count = 0
        self.fps_list = []
        
        print("✅ Inspector initialized!\n")
    
    def process_frame(self, frame):
        """Process a single frame"""
        # Get simulated GPS coordinates
        lat, lon, alt = self.gps_points[self.gps_index % len(self.gps_points)]
        self.gps_index += 1
        
        # Run YOLO inference
        start_time = cv2.getTickCount()
        results = self.model.predict(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]
        end_time = cv2.getTickCount()
        
        # Calculate FPS
        inference_time = (end_time - start_time) / cv2.getTickFrequency()
        fps = 1 / inference_time if inference_time > 0 else 0
        self.fps_list.append(fps)
        
        # Process detections
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            bbox = box.xyxy[0].cpu().numpy().tolist()
            class_name = results.names[cls_id]
            
            # Add GPS-tagged detection
            self.gps_handler.add_detection(
                image_name=f"webcam_frame_{self.frame_count:06d}.jpg",
                class_name=class_name,
                confidence=conf,
                bbox=bbox,
                latitude=lat,
                longitude=lon,
                altitude=alt
            )
            
            self.detection_count += 1
        
        # Draw detections on frame
        annotated_frame = results.plot()
        
        # Add overlay information
        self._draw_overlay(annotated_frame, lat, lon, alt, fps, len(results.boxes))
        
        self.frame_count += 1
        return annotated_frame
    
    def _draw_overlay(self, frame, lat, lon, alt, fps, num_detections):
        """Draw information overlay on frame"""
        h, w = frame.shape[:2]
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Title
        cv2.putText(frame, "🚁 PIPELINE INSPECTION - LAPTOP TESTING", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # GPS coordinates (if enabled)
        if SHOW_GPS:
            cv2.putText(frame, f"GPS: {lat:.6f}, {lon:.6f} | Alt: {alt:.1f}m", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Statistics
        stats_text = []
        if SHOW_FPS:
            stats_text.append(f"FPS: {fps:.1f}")
        if SHOW_DETECTION_COUNT:
            stats_text.append(f"Detections: {self.detection_count}")
        stats_text.append(f"Frame: {self.frame_count}")
        
        cv2.putText(frame, " | ".join(stats_text), 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Mode indicator
        cv2.putText(frame, "MODE: SIMULATED GPS", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Detection indicator
        if num_detections > 0:
            cv2.circle(frame, (w - 30, 30), 15, (0, 0, 255), -1)
            cv2.putText(frame, str(num_detections), (w - 38, 37), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def run(self):
        """Run the webcam inspection"""
        print("="*70)
        print("🎥 STARTING WEBCAM TESTING")
        print("="*70)
        print("Settings from config.py:")
        print(f"  Output Directory: {OUTPUT_DIRECTORY}")
        print(f"  Auto-save interval: {AUTO_SAVE_INTERVAL}")
        print(f"  Frame skip: {FRAME_SKIP}")
        print("\nControls:")
        print("  [Q] - Quit and save results")
        print("  [S] - Save results now")
        print("  [P] - Print statistics")
        print("  [R] - Reset detection counter")
        print("  [SPACE] - Pause/Resume")
        print("="*70 + "\n")
        
        # Create output directory
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        
        # Open webcam
        cap = cv2.VideoCapture(CAMERA_INDEX)
        
        if not cap.isOpened():
            print(f"❌ Error: Could not open webcam {CAMERA_INDEX}")
            print(f"Try changing CAMERA_INDEX in config.py")
            return
        
        # Set webcam properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
        
        print("✅ Webcam opened successfully")
        print("🚀 Inspection started! Press 'Q' to quit.\n")
        
        paused = False
        last_save_count = 0
        frame_counter = 0
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        print("⚠️ Failed to grab frame")
                        break
                    
                    # Frame skipping for performance
                    frame_counter += 1
                    if frame_counter % FRAME_SKIP != 0:
                        continue
                    
                    # Process frame
                    annotated_frame = self.process_frame(frame)
                    
                    # Auto-save periodically
                    if AUTO_SAVE_INTERVAL > 0 and \
                       self.detection_count > 0 and \
                       self.detection_count >= last_save_count + AUTO_SAVE_INTERVAL:
                        self._save_results(auto=True)
                        last_save_count = self.detection_count
                else:
                    # Show paused frame
                    cv2.putText(annotated_frame, "⏸ PAUSED", 
                               (annotated_frame.shape[1]//2 - 100, annotated_frame.shape[0]//2),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
                
                # Display frame
                cv2.imshow('Pipeline Inspection - Webcam Testing', annotated_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n🛑 Quit requested...")
                    break
                elif key == ord('s'):
                    print("\n💾 Manual save requested...")
                    self._save_results(auto=False)
                elif key == ord('p'):
                    print("\n" + "="*70)
                    self.gps_handler.print_summary_report()
                    print("="*70 + "\n")
                elif key == ord('r'):
                    print("\n🔄 Resetting detection counter...")
                    self.detection_count = 0
                    self.gps_handler = GPSTaggedDetection()
                elif key == ord(' '):
                    paused = not paused
                    print(f"\n{'⏸ PAUSED' if paused else '▶️ RESUMED'}")
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user (Ctrl+C)")
        
        finally:
            # Cleanup
            print("\n🧹 Cleaning up...")
            cap.release()
            cv2.destroyAllWindows()
            
            # Final save
            print("\n💾 Saving final results...")
            self._save_results(final=True)
            
            # Print final statistics
            self._print_final_stats()
    
    def _save_results(self, auto=False, final=False):
        """Save detection results based on config settings"""
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
                self.gps_handler.create_interactive_map(f'{OUTPUT_DIRECTORY}/{prefix}detection_map.html')
            
            if auto:
                print(f"💾 Auto-saved: {self.detection_count} detections")
            elif final:
                print(f"✅ Final save complete: {self.detection_count} detections")
            else:
                print(f"💾 Manual save complete: {self.detection_count} detections")
        except Exception as e:
            print(f"⚠️ Error saving results: {e}")
    
    def _print_final_stats(self):
        """Print final statistics"""
        print("\n" + "="*70)
        print("📊 FINAL STATISTICS")
        print("="*70)
        print(f"Total frames processed: {self.frame_count}")
        print(f"Total detections: {self.detection_count}")
        if self.fps_list:
            print(f"Average FPS: {np.mean(self.fps_list):.1f}")
        print("="*70 + "\n")
        
        self.gps_handler.print_summary_report()
        
        print("\n✅ Testing complete!")
        print(f"📁 Results saved to: {os.path.abspath(OUTPUT_DIRECTORY)}/")


def main():
    """Main function"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     🚁 PIPELINE INSPECTION - WEBCAM TESTING SYSTEM 🚁          ║
    ║                                                                ║
    ║     All settings can be changed in config.py                   ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model not found at {MODEL_PATH}")
        print("\nPlease:")
        print("1. Download best.pt from Google Colab after training")
        print(f"2. Place it at: {MODEL_PATH}")
        print("3. Or update MODEL_PATH in config.py")
        return
    
    try:
        # Create and run inspector
        inspector = WebcamPipelineInspector()
        inspector.run()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()