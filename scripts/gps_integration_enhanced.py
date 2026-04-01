# ============================================================================
# ENHANCED GPS INTEGRATION MODULE - WEBCAM FIRST, RASPBERRY PI READY
# ============================================================================

"""
DEVELOPMENT WORKFLOW:
1. Test on laptop with webcam + simulated GPS ✅ (START HERE)
2. Verify all features work correctly
3. Deploy to Raspberry Pi with real GPS (just change 2 parameters)

This module includes:
✅ Simulated GPS for laptop testing
✅ Real GPS for Raspberry Pi
✅ Multiple export formats (JSON, CSV, KML, HTML map, GeoJSON)
✅ Distance traveled calculation
✅ Detection density heatmap
✅ Severity analysis
✅ Maintenance priority ranking
✅ Flight statistics
"""

import json
import csv
from datetime import datetime
import math
from typing import List, Dict, Tuple, Optional
import numpy as np
import os


# ============================================================================
# ENHANCED GPS DATA HANDLER CLASS
# ============================================================================
class GPSTaggedDetection:
    """Handles GPS-tagged detection data with advanced analytics"""
    
    def __init__(self):
        self.detections = []
        self.flight_start_time = None
        self.flight_end_time = None
    
    def add_detection(self, 
                     image_name: str,
                     class_name: str,
                     confidence: float,
                     bbox: List[float],
                     latitude: float,
                     longitude: float,
                     altitude: float = None,
                     timestamp: str = None):
        """Add a GPS-tagged detection"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Track flight time
        if self.flight_start_time is None:
            self.flight_start_time = timestamp
        self.flight_end_time = timestamp
        
        detection = {
            'timestamp': timestamp,
            'image': image_name,
            'class': class_name,
            'confidence': confidence,
            'bbox': bbox,
            'gps': {
                'latitude': latitude,
                'longitude': longitude,
                'altitude': altitude
            },
            'severity': self._classify_severity(class_name)  # NEW: Severity rating
        }
        
        self.detections.append(detection)
    
    def _classify_severity(self, class_name: str) -> str:
        """Classify defect severity for maintenance priority"""
        class_lower = class_name.lower()
        
        if any(x in class_lower for x in ['severe', 'critical', 'car', 'damage']):
            return 'CRITICAL'
        elif any(x in class_lower for x in ['moderate', 'corrosion', 'iron rust']):
            return 'HIGH'
        elif any(x in class_lower for x in ['mild', 'rust', 'copper']):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def save_to_json(self, filepath: str):
        """Save detections to JSON file"""
        output = {
            'metadata': {
                'total_detections': len(self.detections),
                'flight_start': self.flight_start_time,
                'flight_end': self.flight_end_time,
                'generated_at': datetime.now().isoformat()
            },
            'detections': self.detections,
            'statistics': self.get_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"✅ Saved {len(self.detections)} GPS-tagged detections to {filepath}")
    
    def save_to_csv(self, filepath: str):
        """Save detections to CSV file"""
        if not self.detections:
            print("⚠️ No detections to save")
            return
        
        fieldnames = ['timestamp', 'image', 'class', 'confidence', 'severity',
                     'latitude', 'longitude', 'altitude',
                     'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2']
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for det in self.detections:
                row = {
                    'timestamp': det['timestamp'],
                    'image': det['image'],
                    'class': det['class'],
                    'confidence': det['confidence'],
                    'severity': det['severity'],
                    'latitude': det['gps']['latitude'],
                    'longitude': det['gps']['longitude'],
                    'altitude': det['gps'].get('altitude', ''),
                    'bbox_x1': det['bbox'][0],
                    'bbox_y1': det['bbox'][1],
                    'bbox_x2': det['bbox'][2],
                    'bbox_y2': det['bbox'][3]
                }
                writer.writerow(row)
        
        print(f"✅ Saved {len(self.detections)} GPS-tagged detections to {filepath}")
    
    def save_to_kml(self, filepath: str):
        """Save detections as KML for Google Earth visualization"""
        try:
            import simplekml
            
            kml = simplekml.Kml()
            
            # Folders for different severity levels
            folders = {
                'CRITICAL': kml.newfolder(name='🔴 CRITICAL - Immediate Action Required'),
                'HIGH': kml.newfolder(name='🟠 HIGH - Schedule Maintenance Soon'),
                'MEDIUM': kml.newfolder(name='🟡 MEDIUM - Monitor'),
                'LOW': kml.newfolder(name='🟢 LOW - Routine Inspection')
            }
            
            # Color and icon mapping
            severity_styles = {
                'CRITICAL': {'color': simplekml.Color.red, 'icon': 'http://maps.google.com/mapfiles/kml/paddle/red-stars.png'},
                'HIGH': {'color': simplekml.Color.orange, 'icon': 'http://maps.google.com/mapfiles/kml/paddle/orange-circle.png'},
                'MEDIUM': {'color': simplekml.Color.yellow, 'icon': 'http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png'},
                'LOW': {'color': simplekml.Color.green, 'icon': 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png'}
            }
            
            for det in self.detections:
                severity = det['severity']
                folder = folders[severity]
                
                # Create point
                pnt = folder.newpoint(
                    name=f"{det['class']} ({det['confidence']:.0%})",
                    coords=[(det['gps']['longitude'], det['gps']['latitude'], det['gps'].get('altitude', 0))]
                )
                
                # Enhanced description
                pnt.description = f"""
                <![CDATA[
                <h3>Detection Details</h3>
                <table border="1" cellpadding="5">
                <tr><td><b>Severity</b></td><td>{severity}</td></tr>
                <tr><td><b>Class</b></td><td>{det['class']}</td></tr>
                <tr><td><b>Confidence</b></td><td>{det['confidence']:.2%}</td></tr>
                <tr><td><b>Image</b></td><td>{det['image']}</td></tr>
                <tr><td><b>Timestamp</b></td><td>{det['timestamp']}</td></tr>
                <tr><td><b>GPS</b></td><td>{det['gps']['latitude']:.6f}, {det['gps']['longitude']:.6f}</td></tr>
                <tr><td><b>Altitude</b></td><td>{det['gps'].get('altitude', 'N/A')} m</td></tr>
                </table>
                ]]>
                """
                
                # Set style
                style = severity_styles[severity]
                pnt.style.iconstyle.color = style['color']
                pnt.style.iconstyle.icon.href = style['icon']
                pnt.style.iconstyle.scale = 1.5
            
            kml.save(filepath)
            print(f"✅ Saved KML file to {filepath} (open in Google Earth)")
            
        except ImportError:
            print("⚠️ simplekml not installed. Run: pip install simplekml")
    
    def save_to_geojson(self, filepath: str):
        """Save as GeoJSON for web mapping libraries"""
        features = []
        
        for det in self.detections:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [det['gps']['longitude'], det['gps']['latitude'], det['gps'].get('altitude', 0)]
                },
                'properties': {
                    'class': det['class'],
                    'confidence': det['confidence'],
                    'severity': det['severity'],
                    'timestamp': det['timestamp'],
                    'image': det['image']
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        with open(filepath, 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"✅ Saved GeoJSON to {filepath}")
    
    def create_interactive_map(self, filepath: str = 'detection_map.html'):
        """Create enhanced interactive HTML map with clustering and heatmap"""
        try:
            import folium
            from folium import plugins
            
            if not self.detections:
                print("⚠️ No detections to map")
                return
            
            # Calculate center point
            avg_lat = np.mean([d['gps']['latitude'] for d in self.detections])
            avg_lon = np.mean([d['gps']['longitude'] for d in self.detections])
            
            # Create map with multiple basemaps
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=16)
            
            # Add different tile layers
            folium.TileLayer('OpenStreetMap').add_to(m)
            folium.TileLayer('Stamen Terrain').add_to(m)
            folium.TileLayer('Stamen Toner').add_to(m)
            folium.TileLayer('cartodbpositron').add_to(m)
            
            # Layer control
            folium.LayerControl().add_to(m)
            
            # Color mapping by severity
            severity_colors = {
                'CRITICAL': 'red',
                'HIGH': 'orange',
                'MEDIUM': 'yellow',
                'LOW': 'green'
            }
            
            # Marker cluster for better visualization
            marker_cluster = plugins.MarkerCluster().add_to(m)
            
            # Add markers
            for det in self.detections:
                color = severity_colors.get(det['severity'], 'blue')
                
                # Create popup content
                popup_html = f"""
                <div style="width:200px">
                    <h4 style="color:{color}">{det['severity']}</h4>
                    <b>Class:</b> {det['class']}<br>
                    <b>Confidence:</b> {det['confidence']:.2%}<br>
                    <b>Image:</b> {det['image']}<br>
                    <b>Time:</b> {det['timestamp'][:19]}<br>
                    <b>GPS:</b> {det['gps']['latitude']:.6f}, {det['gps']['longitude']:.6f}<br>
                    <b>Altitude:</b> {det['gps'].get('altitude', 'N/A')} m
                </div>
                """
                
                folium.Marker(
                    location=[det['gps']['latitude'], det['gps']['longitude']],
                    popup=folium.Popup(popup_html, max_width=250),
                    icon=folium.Icon(color=color, icon='warning-sign' if det['severity'] in ['CRITICAL', 'HIGH'] else 'info-sign')
                ).add_to(marker_cluster)
            
            # Add heatmap layer
            heat_data = [[d['gps']['latitude'], d['gps']['longitude'], 
                         1.0 if d['severity'] == 'CRITICAL' else 
                         0.7 if d['severity'] == 'HIGH' else 
                         0.4 if d['severity'] == 'MEDIUM' else 0.2] 
                        for d in self.detections]
            
            heat_map = plugins.HeatMap(heat_data, name='Detection Density Heatmap', 
                                      min_opacity=0.3, radius=15, blur=20)
            heat_map.add_to(m)
            
            # Draw flight path
            if len(self.detections) > 1:
                path_coords = [[d['gps']['latitude'], d['gps']['longitude']] for d in self.detections]
                folium.PolyLine(path_coords, color='blue', weight=2, opacity=0.6, 
                               popup='Flight Path').add_to(m)
            
            # Add statistics box
            stats = self.get_statistics()
            stats_html = f"""
            <div style="position: fixed; top: 10px; right: 10px; width: 300px; background: white; 
                        border: 2px solid grey; z-index:9999; padding: 10px; border-radius: 5px;">
                <h4>🚁 Inspection Summary</h4>
                <p><b>Total Detections:</b> {stats['total_detections']}</p>
                <p><b>Distance Covered:</b> {stats['distance_traveled_km']:.2f} km</p>
                <p><b>Coverage Area:</b> {stats['coverage_area_km2']:.4f} km²</p>
                <p><b>Flight Duration:</b> {stats['flight_duration']}</p>
                <hr>
                <p><b>By Severity:</b></p>
                <ul>
                {"".join([f"<li>{sev}: {count}</li>" for sev, count in stats['severity_counts'].items()])}
                </ul>
            </div>
            """
            m.get_root().html.add_child(folium.Element(stats_html))
            
            # Save map
            m.save(filepath)
            print(f"✅ Interactive map saved to {filepath}")
            print(f"   Open in browser: file://{os.path.abspath(filepath)}")
            
        except ImportError:
            print("⚠️ folium not installed. Run: pip install folium")
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS points in km (Haversine formula)"""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_statistics(self):
        """Get comprehensive detection statistics"""
        if not self.detections:
            return {}
        
        # Basic stats
        stats = {
            'total_detections': len(self.detections),
            'classes': {},
            'severity_counts': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'confidence_stats': {
                'mean': np.mean([d['confidence'] for d in self.detections]),
                'min': np.min([d['confidence'] for d in self.detections]),
                'max': np.max([d['confidence'] for d in self.detections]),
                'std': np.std([d['confidence'] for d in self.detections])
            }
        }
        
        # Count by class and severity
        for det in self.detections:
            # Class counts
            class_name = det['class']
            stats['classes'][class_name] = stats['classes'].get(class_name, 0) + 1
            
            # Severity counts
            stats['severity_counts'][det['severity']] += 1
        
        # Calculate distance traveled
        if len(self.detections) > 1:
            total_distance = 0
            for i in range(len(self.detections) - 1):
                lat1 = self.detections[i]['gps']['latitude']
                lon1 = self.detections[i]['gps']['longitude']
                lat2 = self.detections[i+1]['gps']['latitude']
                lon2 = self.detections[i+1]['gps']['longitude']
                total_distance += self.calculate_distance(lat1, lon1, lat2, lon2)
            stats['distance_traveled_km'] = total_distance
        else:
            stats['distance_traveled_km'] = 0
        
        # Coverage area
        stats['coverage_area_km2'] = self._calculate_coverage_area()
        
        # Flight duration
        if self.flight_start_time and self.flight_end_time:
            try:
                start = datetime.fromisoformat(self.flight_start_time)
                end = datetime.fromisoformat(self.flight_end_time)
                duration = end - start
                stats['flight_duration'] = str(duration)
            except:
                stats['flight_duration'] = 'N/A'
        else:
            stats['flight_duration'] = 'N/A'
        
        # Detection density (detections per km)
        if stats['distance_traveled_km'] > 0:
            stats['detection_density'] = stats['total_detections'] / stats['distance_traveled_km']
        else:
            stats['detection_density'] = 0
        
        return stats
    
    def _calculate_coverage_area(self):
        """Calculate approximate coverage area in km²"""
        if len(self.detections) < 3:
            return 0
        
        lats = [d['gps']['latitude'] for d in self.detections]
        lons = [d['gps']['longitude'] for d in self.detections]
        
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        
        # Approximate area
        km_per_degree = 111
        area = lat_range * lon_range * km_per_degree * km_per_degree
        
        return area
    
    def get_maintenance_priorities(self):
        """Generate maintenance priority list"""
        # Group by severity
        priorities = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        for det in self.detections:
            priorities[det['severity']].append({
                'location': f"{det['gps']['latitude']:.6f}, {det['gps']['longitude']:.6f}",
                'class': det['class'],
                'confidence': det['confidence'],
                'timestamp': det['timestamp'],
                'image': det['image']
            })
        
        return priorities
    
    def print_summary_report(self):
        """Print comprehensive summary report"""
        stats = self.get_statistics()
        priorities = self.get_maintenance_priorities()
        
        print("\n" + "="*80)
        print("🚁 PIPELINE INSPECTION SUMMARY REPORT")
        print("="*80)
        
        print(f"\n📊 FLIGHT STATISTICS:")
        print(f"  Flight Duration:       {stats['flight_duration']}")
        print(f"  Distance Traveled:     {stats['distance_traveled_km']:.2f} km")
        print(f"  Coverage Area:         {stats['coverage_area_km2']:.4f} km²")
        print(f"  Detection Density:     {stats['detection_density']:.1f} detections/km")
        
        print(f"\n🔍 DETECTION SUMMARY:")
        print(f"  Total Detections:      {stats['total_detections']}")
        print(f"  Avg Confidence:        {stats['confidence_stats']['mean']:.2%}")
        print(f"  Confidence Range:      {stats['confidence_stats']['min']:.2%} - {stats['confidence_stats']['max']:.2%}")
        
        print(f"\n⚠️ SEVERITY BREAKDOWN:")
        for severity, count in stats['severity_counts'].items():
            if count > 0:
                percentage = (count / stats['total_detections']) * 100
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}[severity]
                print(f"  {emoji} {severity:10s}: {count:3d} ({percentage:5.1f}%)")
        
        print(f"\n📋 DETECTIONS BY CLASS:")
        for class_name, count in sorted(stats['classes'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {class_name:25s}: {count:3d}")
        
        print(f"\n🎯 MAINTENANCE PRIORITIES:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            items = priorities[severity]
            if items:
                print(f"\n  {severity} ({len(items)} locations):")
                for i, item in enumerate(items[:3], 1):  # Show top 3
                    print(f"    {i}. {item['class']} at {item['location']} ({item['confidence']:.0%})")
                if len(items) > 3:
                    print(f"    ... and {len(items)-3} more")
        
        print("\n" + "="*80)


# ============================================================================
# WEBCAM TESTING MODE (START HERE - LAPTOP DEVELOPMENT)
# ============================================================================
def simulate_gps_for_webcam(num_frames: int = 100, 
                           start_lat: float = -7.2575,  # Surabaya
                           start_lon: float = 112.7521,
                           flight_distance_km: float = 0.5):
    """
    Simulate GPS coordinates for webcam testing on laptop
    
    Args:
        num_frames: Number of GPS points to generate
        start_lat: Starting latitude (default: Surabaya, Indonesia)
        start_lon: Starting longitude
        flight_distance_km: Simulated flight distance
    
    Returns:
        List of (lat, lon, alt) tuples
    """
    gps_points = []
    deg_per_km = 1 / 111.0
    max_offset = flight_distance_km * deg_per_km
    
    for i in range(num_frames):
        progress = i / num_frames
        
        # Simulate realistic flight pattern (slight zigzag)
        lat = start_lat + (np.sin(progress * np.pi * 2) * 0.3 + progress) * max_offset
        lon = start_lon + progress * max_offset + np.random.normal(0, max_offset * 0.05)
        alt = 50 + np.random.normal(0, 5)  # 50m altitude ± 5m
        
        gps_points.append((lat, lon, alt))
    
    return gps_points


def test_webcam_with_simulated_gps(model_path: str, 
                                   conf_threshold: float = 0.25,
                                   save_interval: int = 10,
                                   use_webcam: bool = True):
    """
    🎥 LAPTOP TESTING MODE: Webcam + Simulated GPS
    
    This is the STARTING POINT for development!
    Test everything on your laptop before deploying to Raspberry Pi.
    
    Args:
        model_path: Path to trained YOLO model
        conf_threshold: Detection confidence threshold
        save_interval: Save results every N detections
        use_webcam: True for laptop webcam, False for test images
    """
    from ultralytics import YOLO
    import cv2
    
    print("🎥 LAPTOP TESTING MODE")
    print("="*70)
    print("Using: Webcam + Simulated GPS")
    print("This tests the ENTIRE pipeline before Raspberry Pi deployment!")
    print("="*70)
    
    # Load model
    model = YOLO(model_path)
    
    # Initialize GPS handler
    gps_handler = GPSTaggedDetection()
    
    # Simulate GPS flight path
    gps_points = simulate_gps_for_webcam(num_frames=1000)
    gps_index = 0
    detection_count = 0
    
    # Open webcam
    if use_webcam:
        cap = cv2.VideoCapture(0)  # 0 = default webcam
        print("✅ Webcam opened")
    else:
        print("❌ Webcam mode disabled - use test images instead")
        return
    
    print("\n🚀 Starting inspection...")
    print("Controls:")
    print("  - Press 'q' to quit")
    print("  - Press 's' to save current results")
    print("  - Press 'p' to print statistics")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get simulated GPS (cycles through points)
        lat, lon, alt = gps_points[gps_index % len(gps_points)]
        gps_index += 1
        
        # Run inference
        results = model.predict(frame, conf=conf_threshold, verbose=False)[0]
        
        # Process detections
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            bbox = box.xyxy[0].cpu().numpy().tolist()
            class_name = results.names[cls_id]
            
            # Add GPS-tagged detection
            gps_handler.add_detection(
                image_name=f"webcam_frame_{detection_count:06d}.jpg",
                class_name=class_name,
                confidence=conf,
                bbox=bbox,
                latitude=lat,
                longitude=lon,
                altitude=alt
            )
            
            detection_count += 1
        
        # Draw results
        annotated_frame = results.plot()
        
        # Add info overlay
        cv2.putText(annotated_frame, f"GPS: {lat:.6f}, {lon:.6f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Alt: {alt:.1f}m", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Detections: {detection_count}", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, "SIMULATED GPS (Laptop Mode)", 
                   (10, annotated_frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imshow('Pipeline Inspection - Laptop Testing', annotated_frame)
        
        # Auto-save periodically
        if detection_count > 0 and detection_count % save_interval == 0:
            gps_handler.save_to_json('laptop_test_detections.json')
            print(f"💾 Auto-saved {detection_count} detections")
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("📸 Saving results...")
            gps_handler.save_to_json('manual_save_detections.json')
        elif key == ord('p'):
            gps_handler.print_summary_report()
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Final save
    print("\n💾 Saving final results...")
    output_dir = 'webcam_gps_test_results'
    os.makedirs(output_dir, exist_ok=True)
    
    gps_handler.save_to_json(f'{output_dir}/detections.json')
    gps_handler.save_to_csv(f'{output_dir}/detections.csv')
    gps_handler.save_to_kml(f'{output_dir}/detections.kml')
    gps_handler.save_to_geojson(f'{output_dir}/detections.geojson')
    gps_handler.create_interactive_map(f'{output_dir}/detection_map.html')
    
    # Print final report
    gps_handler.print_summary_report()
    
    return gps_handler


# ============================================================================
# RASPBERRY PI DEPLOYMENT MODE (AFTER LAPTOP TESTING)
# ============================================================================
class RaspberryPiGPS:
    """
    🤖 RASPBERRY PI MODE: Real GPS Hardware
    
    Use this AFTER testing on laptop!
    Just change mode='raspberry' in your main script.
    """
    
    def __init__(self, use_gpsd: bool = True):
        """Initialize real GPS on Raspberry Pi"""
        self.use_gpsd = use_gpsd
        self.gps_session = None
        
        if use_gpsd:
            try:
                from gps import gps, WATCH_ENABLE
                self.gps_session = gps(mode=WATCH_ENABLE)
                print("✅ Real GPS connected (Raspberry Pi)")
            except ImportError:
                print("⚠️ gpsd not installed. Run: sudo apt install gpsd && pip install gpsd-py3")
            except Exception as e:
                print(f"⚠️ GPS connection failed: {e}")
    
    def get_position(self):
        """Get current GPS position from hardware"""
        if not self.gps_session:
            return None
        
        try:
            report = self.gps_session.next()
            
            if report['class'] == 'TPV':
                lat = getattr(report, 'lat', None)
                lon = getattr(report, 'lon', None)
                alt = getattr(report, 'alt', None)
                
                if lat is not None and lon is not None:
                    return (lat, lon, alt)
        except Exception as e:
            print(f"GPS read error: {e}")
        
        return None


def run_raspberry_pi_inspection(model_path: str,
                                conf_threshold: float = 0.25,
                                camera_source: int = 0):
    """
    🤖 RASPBERRY PI DEPLOYMENT
    
    Run this on Raspberry Pi with real GPS hardware!
    
    Args:
        model_path: Path to model (best.pt or best.tflite)
        conf_threshold: Detection confidence
        camera_source: Camera index (0 for RPi camera)
    """
    from ultralytics import YOLO
    import cv2
    
    print("🤖 RASPBERRY PI DEPLOYMENT MODE")
    print("="*70)
    print("Using: Real GPS Hardware + Camera")
    print("="*70)
    
    # Load model
    model = YOLO(model_path)
    gps_system = RaspberryPiGPS(use_gpsd=True)
    gps_handler = GPSTaggedDetection()
    
    detection_count = 0
    cap = cv2.VideoCapture(camera_source)
    
    print("🚀 Pipeline inspection started...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get real GPS position
        gps_pos = gps_system.get_position()
        
        if gps_pos is None:
            # No GPS fix
            cv2.putText(frame, "⚠️ WAITING FOR GPS FIX...", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            lat, lon, alt = gps_pos
            
            # Run inference
            results = model.predict(frame, conf=conf_threshold, verbose=False)[0]
            
            # Process detections
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy().tolist()
                class_name = results.names[cls_id]
                
                gps_handler.add_detection(
                    image_name=f"frame_{detection_count:06d}.jpg",
                    class_name=class_name,
                    confidence=conf,
                    bbox=bbox,
                    latitude=lat,
                    longitude=lon,
                    altitude=alt
                )
                
                detection_count += 1
            
            # Draw results
            annotated_frame = results.plot()
            cv2.putText(annotated_frame, f"GPS: {lat:.6f}, {lon:.6f}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Pipeline Inspection - LIVE', annotated_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Save results
    gps_handler.save_to_json('raspberry_inspection.json')
    gps_handler.save_to_csv('raspberry_inspection.csv')
    gps_handler.save_to_kml('raspberry_inspection.kml')
    gps_handler.create_interactive_map('raspberry_inspection_map.html')
    
    return gps_handler


# ============================================================================
# SIMPLE USAGE GUIDE
# ============================================================================
"""
🎯 HOW TO USE THIS MODULE:

STEP 1: LAPTOP TESTING (START HERE!)
-------------------------------------
from gps_integration_enhanced import test_webcam_with_simulated_gps

# Test on your laptop webcam with simulated GPS
results = test_webcam_with_simulated_gps(
    model_path='best.pt',
    conf_threshold=0.25,
    use_webcam=True
)

# Check outputs in: webcam_gps_test_results/
# - detections.json
# - detections.csv  
# - detections.kml (open in Google Earth)
# - detection_map.html (open in browser)


STEP 2: RASPBERRY PI DEPLOYMENT (AFTER LAPTOP TESTING WORKS!)
--------------------------------------------------------------
from gps_integration_enhanced import run_raspberry_pi_inspection

# Run on Raspberry Pi with real GPS
results = run_raspberry_pi_inspection(
    model_path='best.pt',  # or 'best.tflite' for faster inference
    conf_threshold=0.25,
    camera_source=0  # 0 for RPi camera
)

THAT'S IT! Just 2 functions to remember:
1. test_webcam_with_simulated_gps() → Laptop
2. run_raspberry_pi_inspection() → Raspberry Pi
"""