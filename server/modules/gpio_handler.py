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
    def __init__(self, alarm_handler, smoke_detector_pin=11):
        """
        Initialize GPIO handler for smoke detector
        Args:
            alarm_handler: Instance of AlarmHandler for controlling the alarm
            smoke_detector_pin (int): GPIO pin number for smoke detector input
        """
        self.smoke_detector_pin = smoke_detector_pin
        self.alarm_handler = alarm_handler
        self.callbacks = []
        self.is_running = False
        self.last_alarm_trigger_time = 0
        self.alarm_cooldown = 30  # Cooldown period in seconds before triggering alarm again
        
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
            
            # Setup smoke detector pin as input without pull-down resistor
            GPIO.setup(self.smoke_detector_pin, GPIO.IN)
            logger.info(f"Successfully configured GPIO pin {self.smoke_detector_pin} as INPUT")
            
            # Test initial pin read
            initial_state = GPIO.input(self.smoke_detector_pin)
            logger.info(f"Initial state of pin {self.smoke_detector_pin}: {initial_state}")
            
        except Exception as e:
            logger.error(f"Failed to setup GPIO pin {self.smoke_detector_pin}: {str(e)}")
            logger.exception("Detailed GPIO setup error:")
            raise