# modules/gpio_handler.py
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

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GPIOHandler:
    def __init__(self, smoke_detector_pin=11):
        """
        Initialize GPIO handler for smoke detector
        Args:
        smoke_detector_pin (int): GPIO pin number for smoke detector input
        """
        self.smoke_detector_pin = smoke_detector_pin
        self.callbacks = []
        self.is_running = False
        
        # Log GPIO availability
        if GPIO_AVAILABLE:
            logger.info("Real GPIO module detected and imported successfully")
            logger.info(f"GPIO Version: {GPIO.VERSION}")
            logger.info(f"GPIO RPI Board Revision: {GPIO.RPI_REVISION}")
        else:
            logger.warning("Using mock GPIO module - running in development mode")
            
        self.setup_gpio()

    def setup_gpio(self):
        """Setup GPIO pins and initial states"""
        try:
            GPIO.setmode(GPIO.BCM)
            logger.info(f"GPIO mode set to BCM")
            
            # Get current mode to verify
            current_mode = "BCM" if GPIO.getmode() == GPIO.BCM else "BOARD"
            logger.info(f"Verified GPIO mode is: {current_mode}")
            
            # Setup smoke detector pin as input with pull-down resistor
            GPIO.setup(self.smoke_detector_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            logger.info(f"Successfully configured GPIO pin {self.smoke_detector_pin} as INPUT with pull-down resistor")
            
            # Test initial pin read
            initial_state = GPIO.input(self.smoke_detector_pin)
            logger.info(f"Initial state of pin {self.smoke_detector_pin}: {initial_state}")
            
        except Exception as e:
            logger.error(f"Failed to setup GPIO pin {self.smoke_detector_pin}: {str(e)}")
            logger.exception("Detailed GPIO setup error:")
            raise

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

    def _continuous_detection(self):
        """Continuously poll the smoke detector pin"""
        last_state = GPIO.input(self.smoke_detector_pin)
        logger.info(f"Starting continuous detection with initial state: {last_state}")
        
        while self.is_running:
            try:
                current_state = GPIO.input(self.smoke_detector_pin)
                
                if current_state != last_state:
                    logger.info(f"State change detected on pin {self.smoke_detector_pin}: {last_state} -> {current_state}")
                    for callback in self.callbacks:
                        try:
                            callback(current_state)
                        except Exception as e:
                            logger.error(f"Error in callback: {str(e)}")
                    last_state = current_state
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error reading GPIO pin: {str(e)}")
                time.sleep(1)  # Wait longer before retrying on error

    def add_callback(self, callback):
        """Add a callback function to be called when smoke state changes"""
        self.callbacks.append(callback)
        logger.info(f"New callback registered. Total callbacks: {len(self.callbacks)}")

    def get_status(self):
        """Get current status of smoke detector"""
        try:
            status = GPIO.input(self.smoke_detector_pin)
            logger.debug(f"Current pin status: {status}")
            return {
                'smoke_detected': status
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