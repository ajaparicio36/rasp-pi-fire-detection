# modules/alarm_handler.py
import logging
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

class AlarmHandler:
    def __init__(self, alarm_pin=12):
        """
        Initialize the alarm handler
        
        Args:
            alarm_pin (int): GPIO pin number for alarm output
        """
        self.alarm_pin = alarm_pin
        self.is_enabled = True
        self.is_active = False
        
        # Log initialization
        if GPIO_AVAILABLE:
            logger.info("Initializing AlarmHandler with real GPIO")
            logger.info(f"GPIO Version: {GPIO.VERSION}")
        else:
            logger.warning("Initializing AlarmHandler with mock GPIO")
            
        logger.info(f"Initializing alarm on pin {alarm_pin}")
        self.setup_alarm()

    def setup_alarm(self):
        """Setup alarm GPIO pin"""
        try:
            GPIO.setmode(GPIO.BCM)
            logger.info("GPIO mode set to BCM")
            
            GPIO.setup(self.alarm_pin, GPIO.OUT)
            logger.info(f"Successfully configured GPIO pin {self.alarm_pin} as OUTPUT")
            
            # Ensure alarm starts in deactivated state
            GPIO.output(self.alarm_pin, GPIO.LOW)
            logger.info("Alarm initialized in deactivated state")
            
        except Exception as e:
            logger.error(f"Error setting up alarm on GPIO pin {self.alarm_pin}: {str(e)}")
            logger.exception("Alarm setup error details:")
            raise

    def activate(self):
        """Activate the alarm if it's enabled"""
        if self.is_enabled:
            try:
                GPIO.output(self.alarm_pin, GPIO.HIGH)
                self.is_active = True
                logger.warning("🚨 ALARM ACTIVATED 🚨")
                return True
            except Exception as e:
                logger.error(f"Failed to activate alarm: {str(e)}")
                return False
        else:
            logger.info("Alarm activation prevented - alarm is disabled")
            return False

    def deactivate(self):
        """Deactivate the alarm"""
        try:
            GPIO.output(self.alarm_pin, GPIO.LOW)
            self.is_active = False
            logger.info("Alarm deactivated")
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate alarm: {str(e)}")
            return False

    def toggle_enable(self):
        """Toggle whether the alarm can be activated"""
        try:
            self.is_enabled = not self.is_enabled
            state_str = "enabled" if self.is_enabled else "disabled"
            logger.info(f"Alarm system {state_str}")
            
            if not self.is_enabled:
                logger.info("Deactivating alarm due to system disable")
                self.deactivate()
                
            return self.is_enabled
        except Exception as e:
            logger.error(f"Error toggling alarm state: {str(e)}")
            return self.is_enabled

    def get_status(self):
        """Get current status of the alarm"""
        try:
            status = {
                'alarm_active': self.is_active,
                'alarm_enabled': self.is_enabled
            }
            logger.debug(f"Current alarm status: {status}")
            return status
        except Exception as e:
            logger.error(f"Error getting alarm status: {str(e)}")
            return {
                'alarm_active': False,
                'alarm_enabled': False,
                'error': str(e)
            }

    def cleanup(self):
        """Cleanup GPIO resources"""
        try:
            logger.info("Starting alarm cleanup...")
            if self.is_active:
                self.deactivate()
            GPIO.cleanup([self.alarm_pin])
            logger.info(f"GPIO cleanup completed for alarm pin {self.alarm_pin}")
        except Exception as e:
            logger.error(f"Error during alarm cleanup: {str(e)}")