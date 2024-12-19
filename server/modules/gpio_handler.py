import logging
import time
import threading
from collections import deque
from statistics import mean, median
from typing import Optional, List, Callable

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("Running in development mode - GPIO functions will be mocked")
    from modules.mock_gpio import GPIO
    GPIO_AVAILABLE = False

# Setup module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GPIOHandler:
    def __init__(self, 
                 alarm_handler,
                 smoke_detector_pin: int = 11,
                 sample_window: float = 1.0,  # 1 second sampling window
                 sample_rate: float = 0.02,   # 50Hz sampling rate
                 trigger_threshold: float = 0.7,
                 clear_threshold: float = 0.3,
                 min_trigger_duration: float = 0.5  # Minimum smoke duration to trigger
                ):
        self.smoke_detector_pin = smoke_detector_pin
        self.alarm_handler = alarm_handler
        self.callbacks: List[Callable] = []
        self.is_running = False
        
        # Sampling configuration
        self.sample_rate = sample_rate
        samples_per_window = int(sample_window / sample_rate)
        self.voltage_buffer = deque(maxlen=samples_per_window)
        self.filtered_buffer = deque(maxlen=5)  # Stores filtered readings
        
        # Thresholds
        self.trigger_threshold = trigger_threshold
        self.clear_threshold = clear_threshold
        self.min_trigger_duration = min_trigger_duration
        self.trigger_start_time: Optional[float] = None
        
        # State tracking
        self.current_state = False
        self.last_state_change = time.time()
        self.state_change_cooldown = 1.0  # Minimum time between state changes
        
        # Log initialization
        if GPIO_AVAILABLE:
            logger.info("Initializing GPIOHandler with real GPIO")
            logger.info(f"GPIO Version: {GPIO.VERSION}")
        else:
            logger.warning("Initializing GPIOHandler with mock GPIO")
            
        logger.info(f"Initializing smoke detector on pin {smoke_detector_pin}")
        self.setup_gpio()
        
    def setup_gpio(self):
        """Setup GPIO with pull-down resistor to stabilize readings"""
        try:
            GPIO.setmode(GPIO.BCM)
            logger.info("GPIO mode set to BCM")
            
            GPIO.setup(self.smoke_detector_pin, GPIO.IN)
            logger.info(f"Successfully configured GPIO pin {self.smoke_detector_pin} as INPUT")
            
        except Exception as e:
            logger.error(f"Error setting up GPIO pin {self.smoke_detector_pin}: {str(e)}")
            logger.exception("GPIO setup error details:")
            raise
        
    def apply_filters(self, readings: deque) -> float:
        """Apply multiple filtering stages to reduce noise"""
        if not readings:
            return 0.0
            
        # Stage 1: Remove outliers
        sorted_readings = sorted(readings)
        q1, q3 = sorted_readings[len(readings)//4], sorted_readings[3*len(readings)//4]
        iqr = q3 - q1
        valid_readings = [x for x in readings if q1 - 1.5*iqr <= x <= q3 + 1.5*iqr]
        
        # Stage 2: Moving median filter
        if not valid_readings:
            return 0.0
        median_value = median(valid_readings)
        
        # Stage 3: Exponential smoothing
        alpha = 0.3  # Smoothing factor
        if not self.filtered_buffer:
            return median_value
        prev_filtered = self.filtered_buffer[-1]
        return alpha * median_value + (1 - alpha) * prev_filtered
        
    def check_smoke_state(self, filtered_value: float) -> bool:
        """Determine smoke state using hysteresis and minimum duration"""
        current_time = time.time()
        
        # Initialize trigger timer if we cross upper threshold
        if filtered_value >= self.trigger_threshold and self.trigger_start_time is None:
            self.trigger_start_time = current_time
            return self.current_state
            
        # Clear trigger timer if we drop below lower threshold
        if filtered_value <= self.clear_threshold:
            self.trigger_start_time = None
            return False
            
        # Check if we've maintained high state long enough to trigger
        if (self.trigger_start_time is not None and 
            current_time - self.trigger_start_time >= self.min_trigger_duration):
            return True
            
        return self.current_state
        
    def _continuous_detection(self):
        """Improved continuous sampling with better noise handling"""
        while self.is_running:
            try:
                # Read current value
                current_reading = GPIO.input(self.smoke_detector_pin)
                self.voltage_buffer.append(current_reading)
                
                # Only process if we have enough samples
                if len(self.voltage_buffer) >= self.voltage_buffer.maxlen:
                    # Apply filtering
                    filtered_value = self.apply_filters(self.voltage_buffer)
                    self.filtered_buffer.append(filtered_value)
                    
                    # Determine smoke state
                    new_state = self.check_smoke_state(filtered_value)
                    
                    # Handle state changes with cooldown
                    current_time = time.time()
                    if (new_state != self.current_state and 
                        current_time - self.last_state_change >= self.state_change_cooldown):
                        
                        self.current_state = new_state
                        self.last_state_change = current_time
                        
                        # Handle alarm control
                        if new_state:
                            self.alarm_handler.activate()
                        else:
                            self.alarm_handler.deactivate()
                            
                        # Notify callbacks
                        for callback in self.callbacks:
                            try:
                                callback(new_state)
                            except Exception as e:
                                logger.error(f"Callback error: {str(e)}")
                
                time.sleep(self.sample_rate)
                
            except Exception as e:
                logger.error(f"Sampling error: {str(e)}")
                time.sleep(1)
                
    def start_detection(self):
        """Start the detection thread"""
        self.is_running = True
        self.detection_thread = threading.Thread(target=self._continuous_detection)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        logger.info("Smoke detection started")
        
    def stop_detection(self):
        """Stop the detection thread"""
        self.is_running = False
        if hasattr(self, 'detection_thread'):
            self.detection_thread.join()
        logger.info("Smoke detection stopped")
            
    def get_status(self):
        """Get current detector status"""
        status = {
            'smoke_detected': self.current_state,
            'filtered_value': self.filtered_buffer[-1] if self.filtered_buffer else 0.0,
            'raw_readings': list(self.voltage_buffer)
        }
        logger.debug(f"Current detector status: {status}")
        return status
        
    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_detection()
        try:
            GPIO.cleanup([self.smoke_detector_pin])
            logger.info(f"GPIO cleanup completed for smoke detector pin {self.smoke_detector_pin}")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {str(e)}")