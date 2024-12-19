import logging
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("Running in development mode - GPIO functions will be mocked")
    from modules.mock_gpio import GPIO
    GPIO_AVAILABLE = False

import time
import threading
from collections import deque
from statistics import mean
from modules.voltage_logger import VoltageLogger

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GPIOHandler:
    def __init__(self, alarm_handler, smoke_detector_pin=11):
        """Initialize GPIO handler for smoke detector"""
        self.smoke_detector_pin = smoke_detector_pin
        self.alarm_handler = alarm_handler
        self.callbacks = []
        self.is_running = False
        self.last_alarm_trigger_time = 0
        self.alarm_cooldown = 30  # Cooldown period in seconds
        
        # Modified state detection settings
        self.reading_window = deque(maxlen=10)  # Increased from 5 to 10 readings
        self.state_change_threshold = 0.8  # 80% of readings must agree for a state change
        self.read_interval = 0.2  # Increased from 0.1 to 0.2 seconds
        self.stable_count_required = 3  # Number of consistent readings required
        self.current_stable_count = 0
        self.last_stable_state = False
        
        # Rest of initialization code remains the same...

    def get_stable_state(self):
        """Get the current stable state using a moving window of readings"""
        if not self.reading_window or len(self.reading_window) < self.reading_window.maxlen:
            return False
            
        current_average = mean(self.reading_window)
        
        # Check if we're significantly above or below thresholds
        if current_average >= 0.8:
            self.current_stable_count = min(self.current_stable_count + 1, self.stable_count_required)
        elif current_average <= 0.2:
            self.current_stable_count = max(self.current_stable_count - 1, 0)
        else:
            # In between thresholds - maintain current state
            return self.last_stable_state
            
        # Only change state if we've had enough consistent readings
        if self.current_stable_count >= self.stable_count_required:
            self.last_stable_state = True
            return True
        elif self.current_stable_count <= 0:
            self.last_stable_state = False
            return False
            
        return self.last_stable_state

    def handle_smoke_detection(self, state):
        """Handle smoke detection state changes and control alarm"""
        try:
            current_time = time.time()
            alarm_status = self.alarm_handler.get_status()
            
            if state:  # Smoke detected
                # Only trigger if we've been in smoke state for enough readings
                if (self.current_stable_count >= self.stable_count_required and
                    alarm_status.get('alarm_enabled', True) and 
                    not alarm_status.get('alarm_active', False) and 
                    current_time - self.last_alarm_trigger_time >= self.alarm_cooldown):
                    
                    logger.warning("Smoke detected consistently - activating alarm")
                    if self.alarm_handler.activate():
                        self.last_alarm_trigger_time = current_time
                    
            else:  # No smoke detected
                # Only deactivate if we're sure there's no smoke for several readings
                if (alarm_status.get('alarm_active', False) and 
                    self.current_stable_count <= 0 and
                    mean(self.reading_window) < 0.2):  # Extra safety check
                    
                    logger.info("Smoke cleared consistently - deactivating alarm")
                    self.alarm_handler.deactivate()
                
        except Exception as e:
            logger.error(f"Error handling smoke detection: {str(e)}")

    def _continuous_detection(self):
        """Continuously poll the smoke detector pin"""
        last_stable_state = self.get_stable_state()
        logger.info(f"Starting continuous detection with initial state: {last_stable_state}")
        
        while self.is_running:
            try:
                 # Read current pin state
                current_reading = GPIO.input(self.smoke_detector_pin)
                self.reading_window.append(current_reading)
                
                # Get stable state
                current_stable_state = self.get_stable_state()
                window_average = mean(self.reading_window)
                
                # Log the voltage reading
                alarm_status = self.alarm_handler.get_status()
                self.voltage_logger.log_reading(
                    raw_reading=current_reading,
                    stable_state=current_stable_state,
                    window_average=window_average,
                    alarm_active=alarm_status.get('alarm_active', False)
                )
                
                # Check for state change
                if current_stable_state != last_stable_state:
                    logger.info(f"State change detected on pin {self.smoke_detector_pin}: {last_stable_state} -> {current_stable_state}")
                    # Handle smoke detection first
                    self.handle_smoke_detection(current_stable_state)
                    # Then notify other callbacks
                    for callback in self.callbacks:
                        try:
                            callback(current_stable_state)
                        except Exception as e:
                            logger.error(f"Error in callback: {str(e)}")
                    last_stable_state = current_stable_state
                
                time.sleep(self.read_interval)
            except Exception as e:
                logger.error(f"Error reading GPIO pin: {str(e)}")
                time.sleep(1)  # Wait longer before retrying on error

    def start_detection(self):
        """Start continuous smoke detection in a separate thread"""
        self.is_running = True
        self.detection_thread = threading.Thread(target=self._continuous_detection)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        logger.info("Smoke detection thread started")

    def stop_detection(self):
        """Stop continuous smoke detection"""
        self.is_running = False
        if hasattr(self, 'detection_thread'):
            self.detection_thread.join()
            logger.info("Smoke detection thread stopped")

    def add_callback(self, callback):
        """Add a callback function to be called when smoke state changes"""
        self.callbacks.append(callback)
        logger.info(f"New callback registered. Total callbacks: {len(self.callbacks)}")

    def get_status(self):
        """Get current status of smoke detector"""
        try:
            stable_state = self.get_stable_state()
            logger.debug(f"Current stable state: {stable_state}")
            return {
                'smoke_detected': stable_state
            }
        except Exception as e:
            logger.error(f"Error reading pin status: {str(e)}")
            return {
                'smoke_detected': None,
                'error': str(e)
            }

    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_detection()
        try:
            GPIO.cleanup([self.smoke_detector_pin])
            logger.info(f"GPIO cleanup completed for pin {self.smoke_detector_pin}")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {str(e)}")