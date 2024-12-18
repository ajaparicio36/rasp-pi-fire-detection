# modules/gpio_handler.py
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Running in development mode - GPIO functions will be mocked")
    from modules.mock_gpio import GPIO

class GPIOHandler:
    def __init__(self, smoke_detector_pin=12):
        """
        Initialize GPIO handler for smoke detector

        Args:
            smoke_detector_pin (int): GPIO pin number for smoke detector input
        """
        self.smoke_detector_pin = smoke_detector_pin
        self.setup_gpio()
        self.callbacks = []

    def setup_gpio(self):
        """Setup GPIO pins and initial states"""
        GPIO.setmode(GPIO.BCM)

        # Setup smoke detector pin as input with pull-down resistor
        try:
            GPIO.setup(self.smoke_detector_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        except RuntimeError as e:
            print(f"Error setting up GPIO pin {self.smoke_detector_pin} as input: {str(e)}")
            raise
        except ValueError as e:
            print(f"Invalid GPIO pin number {self.smoke_detector_pin}: {str(e)}")
            raise

        # Add event detection for smoke detector
        try:
            GPIO.add_event_detect(
                self.smoke_detector_pin,
                GPIO.BOTH,
                callback=self._handle_smoke_detection,
                bouncetime=300
            )
        except RuntimeError as e:
            print(f"Error setting up GPIO event detection on pin {self.smoke_detector_pin}: {str(e)}")
            raise
        except ValueError as e:
            print(f"Invalid GPIO pin number {self.smoke_detector_pin} for event detection: {str(e)}")
            raise

    def add_callback(self, callback):
        """Add a callback function to be called when smoke is detected"""
        self.callbacks.append(callback)

    def _handle_smoke_detection(self, _):
        """
        Callback function for smoke detection events
        Args:
            channel: The GPIO channel that triggered the event
        """
        is_smoke_detected = GPIO.input(self.smoke_detector_pin)
        for callback in self.callbacks:
            callback(is_smoke_detected)

    def get_status(self):
        """Get current status of smoke detector"""
        return {
            'smoke_detected': GPIO.input(self.smoke_detector_pin)
        }

    def cleanup(self):
        """Cleanup GPIO resources"""
        GPIO.cleanup([self.smoke_detector_pin])