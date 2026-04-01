#!/usr/bin/env python3
"""
WEBCAM TESTING SCRIPT FOR LAPTOP
Test your pipeline inspection system before Raspberry Pi deployment

Author: Kris
Project: Drone Pipeline Visual Inspection with GPS
"""

import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
import os
import json

# Import our GPS module
# Make sure gps_integration_enhanced.py is in the same folder
try:
    from gps_integration_enhanced import GPSTaggedDetection, simulate_gps_for_webcam
    print("✅ GPS integration module loaded")
except ImportError:
    print("⚠️ GPS module not found. Make sure gps_integration_enhanced.py is in the same folder!")
    exit(1)


class WebcamPipelineInspector:
    """Main class for webcam testing"""
    
    def __init__(self, model_path, conf_threshold=0.25):
        """
        Initialize the inspector
        
        Args:
            model_path: Path to trained YOLO model (e.g., 'models/best.pt')
            conf_threshold: Confidence threshold for detections
        """
        print("🚀 Initializing Pipeline Inspector...")
        
        # Load YOLO model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        print(f"📦 Loading model from {model_path}")
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        
        # Initialize GPS handler
        self.gps_handler = GPSTaggedDetection()
        
        # Simulate GPS flight path
        print("🛰️ Generating simulated GPS coordinates...")
        self.gps_points = simulate_gps_for_webcam(
            num_frames=1000,
            start_lat=-7.2575,   # Surabaya, Indonesia
            start_lon=112.7521,
            flight_distance_km=0.5
        )
        self.gps_index = 0
        
        # Statistics
        self.frame_count = 0
        self.detection_count = 0
        self.fps_list = []
        
        print("✅ Inspector initialized!")
    
    def process_frame(self, frame):
        """
        Process a single frame: run inference + add GPS tags
        
        Args:
            frame: OpenCV frame from webcam
            
        Returns:
            annotated_frame: Frame with detections drawn
        """
        # Get simulated GPS coordinates
        lat, lon, alt = self.gps_points[self.gps_index % len(self.gps_points)]
        self.gps_index += 1
        
        # Run YOLO inference
        start_time = cv2.getTickCount()
        results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)[0]
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
        
        # Semi-transparent background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Title
        cv2.putText(frame, "🚁 PIPELINE INSPECTION - LAPTOP TESTING", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # GPS coordinates
        cv2.putText(frame, f"GPS: {lat:.6f}, {lon:.6f}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Altitude
        cv2.putText(frame, f"Altitude: {alt:.1f}m", 
                   (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Statistics
        cv2.putText(frame, f"FPS: {fps:.1f} | Detections: {self.detection_count} | Frame: {self.frame_count}", 
                   (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Mode indicator
        cv2.putText(frame, "MODE: SIMULATED GPS", 
                   (10, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Detection indicator (if any detections in current frame)
        if num_detections > 0:
            cv2.circle(frame, (w - 30, 30), 15, (0, 0, 255), -1)
            cv2.putText(frame, str(num_detections), (w - 38, 37), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def run(self, camera_index=0, save_interval=10, output_dir='results'):
        """
        Run the webcam inspection
        
        Args:
            camera_index: Webcam index (usually 0 for default webcam)
            save_interval: Auto-save results every N detections
            output_dir: Directory to save results
        """
        print("\n" + "="*70)
        print("🎥 STARTING WEBCAM TESTING")
        print("="*70)
        print(f"Model: {self.model.ckpt_path if hasattr(self.model, 'ckpt_path') else 'loaded'}")
        print(f"Confidence Threshold: {self.conf_threshold}")
        print(f"Output Directory: {output_dir}")
        print("\nControls:")
        print("  [Q] - Quit and save results")
        print("  [S] - Save results now")
        print("  [P] - Print statistics")
        print("  [R] - Reset detection counter")
        print("  [SPACE] - Pause/Resume")
        print("="*70 + "\n")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Open webcam
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ Error: Could not open webcam {camera_index}")
            print("Try changing camera_index in the script (0, 1, 2...)")
            return
        
        # Set webcam properties (optional)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        print("✅ Webcam opened successfully")
        print("🚀 Inspection started! Press 'Q' to quit.\n")
        
        paused = False
        last_save_count = 0
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        print("⚠️ Failed to grab frame")
                        break
                    
                    # Process frame
                    annotated_frame = self.process_frame(frame)
                    
                    # Auto-save periodically
                    if self.detection_count > 0 and \
                       self.detection_count >= last_save_count + save_interval:
                        self._save_results(output_dir, auto=True)
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
                    self._save_results(output_dir, auto=False)
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
            self._save_results(output_dir, final=True)
            
            # Print final statistics
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
            print(f"📁 Results saved to: {os.path.abspath(output_dir)}/")
    
    def _save_results(self, output_dir, auto=False, final=False):
        """Save detection results to files"""
        prefix = "final_" if final else ""
        
        try:
            self.gps_handler.save_to_json(f'{output_dir}/{prefix}detections.json')
            self.gps_handler.save_to_csv(f'{output_dir}/{prefix}detections.csv')
            self.gps_handler.save_to_kml(f'{output_dir}/{prefix}detections.kml')
            self.gps_handler.save_to_geojson(f'{output_dir}/{prefix}detections.geojson')
            self.gps_handler.create_interactive_map(f'{output_dir}/{prefix}detection_map.html')
            
            if auto:
                print(f"💾 Auto-saved: {self.detection_count} detections")
            elif final:
                print(f"✅ Final save complete: {self.detection_count} detections")
            else:
                print(f"💾 Manual save complete: {self.detection_count} detections")
        except Exception as e:
            print(f"⚠️ Error saving results: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function - Run this to start testing!"""
    
    # Configuration
    MODEL_PATH = 'models/best.pt'          # Path to your trained model
    CONFIDENCE_THRESHOLD = 0.25            # Detection confidence (0.0 - 1.0)
    CAMERA_INDEX = 0                       # Webcam index (try 0, 1, 2 if 0 doesn't work)
    SAVE_INTERVAL = 10                     # Auto-save every N detections
    OUTPUT_DIR = 'results'                 # Where to save results
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     🚁 PIPELINE INSPECTION - WEBCAM TESTING SYSTEM 🚁          ║
    ║                                                                ║
    ║     Testing corrosion detection with simulated GPS             ║
    ║     Before Raspberry Pi deployment                             ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model not found at {MODEL_PATH}")
        print("\nPlease download your trained model from Google Colab:")
        print("1. After training, in Colab run:")
        print("   from google.colab import files")
        print("   files.download('runs/detect/rust_detection_v1/weights/best.pt')")
        print(f"2. Save it to: {MODEL_PATH}")
        return
    
    try:
        # Create inspector
        inspector = WebcamPipelineInspector(
            model_path=MODEL_PATH,
            conf_threshold=CONFIDENCE_THRESHOLD
        )
        
        # Run testing
        inspector.run(
            camera_index=CAMERA_INDEX,
            save_interval=SAVE_INTERVAL,
            output_dir=OUTPUT_DIR
        )
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()