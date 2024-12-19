# modules/gpio_handler.py
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Running in development mode - GPIO functions will be mocked")
    from modules.mock_gpio import GPIO

import time
import threading

class GPIOHandler:
    def __init__(self, smoke_detector_pin=17):
        """
        Initialize GPIO handler for smoke detector
        Args:
        smoke_detector_pin (int): GPIO pin number for smoke detector input
        """
        self.smoke_detector_pin = smoke_detector_pin
        self.callbacks = []
        self.is_running = False
        self.setup_gpio()

    def setup_gpio(self):
        """Setup GPIO pins and initial states"""
        GPIO.setmode(GPIO.BCM)
        # Setup smoke detector pin as input with pull-down resistor
        try:
            GPIO.setup(self.smoke_detector_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        except Exception as e:
            print(f"Error setting up GPIO pin {self.smoke_detector_pin}: {str(e)}")
            raise

    def start_detection(self):
        """Start continuous smoke detection in a separate thread"""
        self.is_running = True
        self.detection_thread = threading.Thread(target=self._continuous_detection)
        self.detection_thread.daemon = True
        self.detection_thread.start()

    def stop_detection(self):
        """Stop continuous smoke detection"""
        self.is_running = False
        if hasattr(self, 'detection_thread'):
            self.detection_thread.join()

    def _continuous_detection(self):
        """Continuously poll the smoke detector pin"""
        last_state = GPIO.input(self.smoke_detector_pin)
        while self.is_running:
            current_state = GPIO.input(self.smoke_detector_pin)
            
            if current_state != last_state:
                # State has changed
                for callback in self.callbacks:
                    callback(current_state)
                last_state = current_state
            
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage

    def add_callback(self, callback):
        """Add a callback function to be called when smoke state changes"""
        self.callbacks.append(callback)

    def get_status(self):
        """Get current status of smoke detector"""
        return {
            'smoke_detected': GPIO.input(self.smoke_detector_pin)
        }

    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_detection()
        GPIO.cleanup([self.smoke_detector_pin])