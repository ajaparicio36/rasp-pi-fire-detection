# modules/data_handler.py
from datetime import datetime
import threading
import time
import json

class DataHandler:
    def __init__(self, gpio_handler, alarm_handler, interval=1.0):
        """
        Initialize the data handler
        
        Args:
            gpio_handler: Instance of GPIOHandler to get smoke detector data
            alarm_handler: Instance of AlarmHandler
            interval (float): Data collection interval in seconds
        """
        self.gpio_handler = gpio_handler
        self.alarm_handler = alarm_handler
        self.interval = interval
        self.is_running = False
        self.data_points = []
        self.max_data_points = 100  # Keep last 100 readings
        
    def start(self, socketio):
        """Start collecting and sending data"""
        self.socketio = socketio
        self.is_running = True
        self.thread = threading.Thread(target=self._collect_data)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop collecting data"""
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join()
            
    def _collect_data(self):
        """Collect data at specified intervals and emit to frontend"""
        while self.is_running:
            try:
                # Get current status
                status = self.gpio_handler.get_status()
                
                # Create data point
                data_point = {
                    'timestamp': datetime.now().isoformat(),
                    'smoke_detected': status['smoke_detected'],
                    'alarm_active': status['alarm_active'],
                    'alarm_enabled': status['alarm_enabled']
                }
                
                # Add to data points list
                self.data_points.append(data_point)
                
                # Keep only the last max_data_points
                if len(self.data_points) > self.max_data_points:
                    self.data_points.pop(0)
                
                # Emit current data point and full dataset
                self.socketio.emit('new_data_point', data_point)
                self.socketio.emit('full_dataset', {
                    'data': self.data_points,
                    'summary': self._generate_summary()
                })
                
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"Error collecting data: {str(e)}")
                time.sleep(self.interval)

    def _generate_summary(self):
        """Generate summary statistics from collected data"""
        if not self.data_points:
            return {
                'smoke_detections': 0,
                'alarm_activations': 0,
                'uptime': 0
            }

        first_timestamp = datetime.fromisoformat(self.data_points[0]['timestamp'])
        last_timestamp = datetime.fromisoformat(self.data_points[-1]['timestamp'])
        
        return {
            'smoke_detections': sum(1 for point in self.data_points if point['smoke_detected']),
            'alarm_activations': sum(1 for point in self.data_points if point['alarm_active']),
            'uptime': (last_timestamp - first_timestamp).total_seconds()
        }

    def get_current_data(self):
        """Get the current dataset and summary"""
        return {
            'data': self.data_points,
            'summary': self._generate_summary()
        }