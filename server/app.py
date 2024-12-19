import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from modules.camera import CameraHandler
from modules.gpio_handler import GPIOHandler
from modules.alarm_handler import AlarmHandler
from modules.data_handler import DataHandler

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/smoke_detector.log',
            maxBytes=1024*1024,  # 1MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

# Get logger for this file
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logger.info("Initializing application components...")

# Initialize handlers
try:
    camera_handler = CameraHandler(fps=5)
    logger.info("Camera handler initialized")
    
    alarm_handler = AlarmHandler()
    logger.info("Alarm handler initialized")
    
    gpio_handler = GPIOHandler()
    logger.info("GPIO handler initialized")
    
    data_handler = DataHandler(gpio_handler, alarm_handler, interval=1.0)
    logger.info("Data handler initialized")
except Exception as e:
    logger.error(f"Error during component initialization: {str(e)}")
    logger.exception("Initialization error details:")
    raise

def handle_smoke_detection(is_smoke_detected):
    """Callback for smoke detection events"""
    try:
        if is_smoke_detected:
            logger.warning("Smoke detected! Activating alarm...")
            alarm_handler.activate()
        else:
            logger.info("Smoke cleared. Deactivating alarm...")
            alarm_handler.deactivate()
        
        # Emit status update
        status = {
            **gpio_handler.get_status(),
            **alarm_handler.get_status()
        }
        socketio.emit('status_update', status)
        logger.debug(f"Emitted status update: {status}")
    except Exception as e:
        logger.error(f"Error in smoke detection handler: {str(e)}")

# Register smoke detection callback
gpio_handler.add_callback(handle_smoke_detection)
logger.info("Smoke detection callback registered")

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    try:
        camera_handler.start(socketio)
        data_handler.start(socketio)
        gpio_handler.start_detection()
        
        # Send initial status
        status = {
            **gpio_handler.get_status(),
            **alarm_handler.get_status()
        }
        socketio.emit('status_update', status)
        socketio.emit('full_dataset', data_handler.get_current_data())
        logger.debug("Sent initial status and dataset to client")
    except Exception as e:
        logger.error(f"Error during client connection handling: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")
    try:
        camera_handler.stop()
        data_handler.stop()
        gpio_handler.stop_detection()
        logger.info("All handlers stopped successfully")
    except Exception as e:
        logger.error(f"Error during disconnect handling: {str(e)}")

@socketio.on('toggle_alarm')
def handle_toggle_alarm():
    try:
        logger.info("Received alarm toggle request")
        enabled = alarm_handler.toggle_enable()
        status = {'alarm_enabled': enabled}  # Match the frontend property name
        logger.info(f"Alarm toggled - new state: {status}")
        socketio.emit('alarm_status', status)
        
        # Also emit a full status update
        full_status = {
            **gpio_handler.get_status(),
            **alarm_handler.get_status()
        }
        logger.info(f"Emitting full status update: {full_status}")
        socketio.emit('status_update', full_status)
    except Exception as e:
        logger.error(f"Error toggling alarm: {str(e)}")

        
@socketio.on('get_status')
def handle_get_status():
    try:
        status = {
            **gpio_handler.get_status(),
            **alarm_handler.get_status()
        }
        socketio.emit('status_update', status)
        logger.debug(f"Status request fulfilled: {status}")
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")

if __name__ == '__main__':
    logger.info("Starting smoke detector application...")
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Error during application runtime: {str(e)}")
        logger.exception("Runtime error details:")
    finally:
        logger.info("Cleaning up resources...")
        try:
            gpio_handler.cleanup()
            alarm_handler.cleanup()
            data_handler.stop()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")