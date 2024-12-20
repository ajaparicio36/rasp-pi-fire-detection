from datetime import datetime
import threading
import time
import json
import logging
from functools import wraps
from typing import Dict, Any

# Setup module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def rate_limited_logging(interval: float):
    """
    Decorator to rate limit logging calls
    
    Args:
        interval (float): Minimum time between logs in seconds
    """
    def decorator(func):
        last_log_time: Dict[str, float] = {}
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            current_time = time.time()
            # Get unique key for each logging type
            log_key = f"{func.__name__}_{args[0] if args else ''}"
            
            # Check if enough time has passed since last log
            if (log_key not in last_log_time or 
                current_time - last_log_time[log_key] >= interval):
                last_log_time[log_key] = current_time
                return func(self, *args, **kwargs)
            return None
        return wrapper
    return decorator

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
        
        self._rate_limited_info("Initializing DataHandler with {} max data points".format(self.max_data_points))
        self._rate_limited_info("Data collection interval set to {} seconds".format(interval))
        
    @rate_limited_logging(10.0)
    def _rate_limited_info(self, message: str) -> None:
        """Rate-limited info logging"""
        logger.info(message)
        
    @rate_limited_logging(10.0)
    def _rate_limited_warning(self, message: str) -> None:
        """Rate-limited warning logging"""
        logger.warning(message)
        
    @rate_limited_logging(10.0)
    def _rate_limited_error(self, message: str) -> None:
        """Rate-limited error logging"""
        logger.error(message)
        
    @rate_limited_logging(10.0)
    def _rate_limited_debug(self, message: str) -> None:
        """Rate-limited debug logging"""
        logger.debug(message)
        
    def start(self, socketio):
        """Start collecting and sending data"""
        try:
            self._rate_limited_info("Starting data collection service...")
            self.socketio = socketio
            self.is_running = True
            self.thread = threading.Thread(target=self._collect_data)
            self.thread.daemon = True
            self.thread.start()
            self._rate_limited_info("Data collection thread started successfully")
        except Exception as e:
            self._rate_limited_error(f"Failed to start data collection: {str(e)}")
            logger.exception("Data collection start error details:")
            raise
        
    def stop(self):
        """Stop collecting data"""
        try:
            self._rate_limited_info("Stopping data collection service...")
            self.is_running = False
            if hasattr(self, 'thread'):
                self.thread.join()
                self._rate_limited_info("Data collection thread stopped successfully")
        except Exception as e:
            self._rate_limited_error(f"Error stopping data collection: {str(e)}")
            
    def _collect_data(self):
        """Collect data at specified intervals and emit to frontend"""
        self._rate_limited_info("Starting data collection loop")
        while self.is_running:
            try:
                # Get current status from both GPIO handler and alarm handler
                gpio_status = self.gpio_handler.get_status()
                alarm_status = self.alarm_handler.get_status()

                # Create data point
                data_point = {
                    'timestamp': datetime.now().isoformat(),
                    'smoke_detected': gpio_status['smoke_detected'],
                    'alarm_active': alarm_status.get('alarm_active', False),
                    'alarm_enabled': alarm_status.get('alarm_enabled', True)
                }

                # Add to data points list
                self.data_points.append(data_point)
                
                if data_point['smoke_detected']:
                    self._rate_limited_warning("Smoke detection recorded in data point")
                if data_point['alarm_active']:
                    self._rate_limited_warning("Alarm activation recorded in data point")

                # Keep only the last max_data_points
                if len(self.data_points) > self.max_data_points:
                    self.data_points.pop(0)
                    self._rate_limited_debug("Removed oldest data point to maintain maximum limit")

                # Generate summary before emitting
                summary = self._generate_summary()
                
                # Emit current data point and full dataset
                self.socketio.emit('new_data_point', data_point)
                self.socketio.emit('full_dataset', {
                    'data': self.data_points,
                    'summary': summary
                })
                
                self._rate_limited_debug(f"Emitted new data point: {data_point}")
                self._rate_limited_debug(f"Current summary: {summary}")

                time.sleep(self.interval)
            except Exception as e:
                self._rate_limited_error(f"Error in data collection cycle: {str(e)}")
                logger.exception("Data collection error details:")
                time.sleep(self.interval)

    def _generate_summary(self):
        """Generate summary statistics from collected data"""
        try:
            if not self.data_points:
                self._rate_limited_debug("No data points available for summary generation")
                return {
                    'smoke_detections': 0,
                    'alarm_activations': 0,
                    'uptime': 0
                }

            first_timestamp = datetime.fromisoformat(self.data_points[0]['timestamp'])
            last_timestamp = datetime.fromisoformat(self.data_points[-1]['timestamp'])
            
            summary = {
                'smoke_detections': sum(1 for point in self.data_points if point['smoke_detected']),
                'alarm_activations': sum(1 for point in self.data_points if point['alarm_active']),
                'uptime': (last_timestamp - first_timestamp).total_seconds()
            }
            
            self._rate_limited_debug(f"Generated summary statistics: {summary}")
            return summary
            
        except Exception as e:
            self._rate_limited_error(f"Error generating summary: {str(e)}")
            logger.exception("Summary generation error details:")
            return {
                'smoke_detections': 0,
                'alarm_activations': 0,
                'uptime': 0,
                'error': str(e)
            }

    def get_current_data(self):
        """Get the current dataset and summary"""
        try:
            self._rate_limited_debug("Retrieving current dataset and summary")
            current_data = {
                'data': self.data_points,
                'summary': self._generate_summary()
            }
            return current_data
        except Exception as e:
            self._rate_limited_error(f"Error retrieving current data: {str(e)}")
            return {
                'data': [],
                'summary': {
                    'smoke_detections': 0,
                    'alarm_activations': 0,
                    'uptime': 0,
                    'error': str(e)
                }
            }