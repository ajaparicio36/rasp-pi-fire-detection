import cv2
import base64
import torch
import os
import numpy as np
from threading import Thread
import time

class CameraHandler:
    def __init__(self, camera_index_range=(0, 3), fps=10, model_path='model/yolov5s_best.pt'):
        self.camera_index_range = camera_index_range
        self.camera = None
        self.camera_available = False
        self.fps = fps
        self.frame_interval = 1 / fps
        self.is_running = False
        self.model_path = os.path.abspath(model_path)
        self.model = None
        self.fire_detected = False
        self.fire_confidence = 0.0

        self.find_available_camera()

    def find_available_camera(self):
        for index in range(self.camera_index_range[0], self.camera_index_range[1] + 1):
            self.camera = cv2.VideoCapture(index)
            if self.camera.isOpened():
                print(f"Camera found at index {index}")
                self.camera_available = True
                break
            else:
                self.camera.release()
                self.camera = None

        if not self.camera_available:
            print("No camera found in the given range.")

        if not os.path.exists(self.model_path):
            print(f"Warning: Model file not found at {self.model_path}")
            print("Fire detection will be disabled.")
            self.model = None
        else:
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
            except Exception as e:
                print(f"Error loading YOLOv5 model: {e}")
                print("Fire detection will be disabled.")
                self.model = None

    def start(self, socketio):
        if self.camera_available:
            self.is_running = True
            self.thread = Thread(target=self._stream_frames, args=(socketio,))
            self.thread.daemon = True
            self.thread.start()
        else:
            print("No camera available, cannot start the feed.")

    # Rest of the code remains the same
        
    def stop(self):
        """Stop the camera feed"""
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join()
    
    def _stream_frames(self, socketio):
        """Stream frames at specified FPS with fire detection"""
        while self.is_running:
            start_time = time.time()
            
            success, frame = self.camera.read()
            if not success:
                continue
            
            # Reset fire detection state
            self.fire_detected = False
            self.fire_confidence = 0.0
            
            # Perform fire detection if model is loaded
            if self.model is not None:
                try:
                    # Perform fire detection
                    results = self.model(frame)
                    
                    # Process detections
                    for *xyxy, conf, cls in results.xyxy[0]:
                        # Convert coordinates to integers
                        xyxy = [int(x) for x in xyxy]
                        
                        # Draw bounding box
                        cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 255, 0), 2)
                        
                        # Update fire detection state
                        self.fire_detected = True
                        self.fire_confidence = float(conf)
                        
                        # Add label with confidence
                        label = f'Fire: {conf:.2f}'
                        cv2.putText(frame, label, (xyxy[0], xyxy[1] - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                except Exception as e:
                    print(f"Error during fire detection: {e}")
            
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = base64.b64encode(buffer).decode('utf-8')
            
            # Emit the frame with fire detection information
            socketio.emit('camera_frame', {
                'frame': frame_bytes,
                'fire_detected': self.fire_detected,
                'fire_confidence': self.fire_confidence,
                'model_loaded': self.model is not None
            })
            
            # Maintain FPS
            processing_time = time.time() - start_time
            if processing_time < self.frame_interval:
                time.sleep(self.frame_interval - processing_time)
    
    def __del__(self):
        """Clean up resources"""
        self.stop()
        self.camera.release()
    
    def is_fire_detected(self):
        """
        Check if fire is currently detected
        
        Returns:
        - Tuple (fire_detected, confidence)
        """
        return self.fire_detected, self.fire_confidence