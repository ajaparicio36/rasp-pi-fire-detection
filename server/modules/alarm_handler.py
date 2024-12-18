# modules/alarm_handler.py
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Running in development mode - GPIO functions will be mocked")
    from modules.mock_gpio import GPIO



class AlarmHandler:
    def __init__(self, alarm_pin=11):
        """
        Initialize the alarm handler
        
        Args:
            alarm_pin (int): GPIO pin number for alarm output
        """
        self.alarm_pin = alarm_pin
        self.is_enabled = True
        self.is_active = False
        self.setup_alarm()

    def setup_alarm(self):
        """Setup alarm GPIO pin"""
        GPIO.setmode(GPIO.BCM)
        try:
            GPIO.setup(self.alarm_pin, GPIO.OUT)
        except RuntimeError as e:
            print(f"Error setting up GPIO pin {self.alarm_pin}: {str(e)}")
            # Handle the error, e.g., use a different pin or log the issue
            GPIO.output(self.alarm_pin, GPIO.LOW)

    def activate(self):
        """Activate the alarm if it's enabled"""
        if self.is_enabled:
            GPIO.output(self.alarm_pin, GPIO.HIGH)
            self.is_active = True
            return True
        return False

    def deactivate(self):
        """Deactivate the alarm"""
        GPIO.output(self.alarm_pin, GPIO.LOW)
        self.is_active = False
        return True

    def toggle_enable(self):
        """Toggle whether the alarm can be activated"""
        self.is_enabled = not self.is_enabled
        if not self.is_enabled:
            self.deactivate()
        return self.is_enabled

    def get_status(self):
        """Get current status of the alarm"""
        return {
            'is_active': self.is_active,
            'is_enabled': self.is_enabled
        }

    def cleanup(self):
        """Cleanup GPIO resources"""
        self.deactivate()
        GPIO.cleanup([self.alarm_pin])