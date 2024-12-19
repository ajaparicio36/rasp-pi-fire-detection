import csv
import time
from datetime import datetime
import os

class VoltageLogger:
    def __init__(self, log_file=None):
        """
        Initialize voltage logger
        Args:
            log_file (str): Path to CSV file for logging. If None, uses default path
        """
        if log_file is None:
            # Create logs directory if it doesn't exist (matching your app.py structure)
            os.makedirs('logs', exist_ok=True)
            self.log_file = os.path.join('logs', 'smoke_detector_voltage.csv')
        else:
            self.log_file = log_file
            
        self.setup_csv()
        
    def setup_csv(self):
        """Setup CSV file with headers"""
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'raw_reading', 'stable_state', 'window_average', 'alarm_active'])
            
    def log_reading(self, raw_reading, stable_state, window_average, alarm_active):
        """Log a single reading with timestamp"""
        timestamp = datetime.now().isoformat()
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, raw_reading, stable_state, window_average, alarm_active])