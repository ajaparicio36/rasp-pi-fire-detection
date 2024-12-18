from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from modules.camera import CameraHandler
from modules.gpio_handler import GPIOHandler
from modules.alarm_handler import AlarmHandler
from modules.data_handler import DataHandler

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize handlers
camera_handler = CameraHandler(fps=10)
alarm_handler = AlarmHandler(alarm_pin=17)
gpio_handler = GPIOHandler(smoke_detector_pin=18)
data_handler = DataHandler(gpio_handler, alarm_handler, interval=1.0)

def handle_smoke_detection(is_smoke_detected):
    """Callback for smoke detection events"""
    if is_smoke_detected:
        alarm_handler.activate()
    else:
        alarm_handler.deactivate()
    
    # Emit status update
    status = {
        **gpio_handler.get_status(),
        **alarm_handler.get_status()
    }
    socketio.emit('status_update', status)

# Register smoke detection callback
gpio_handler.add_callback(handle_smoke_detection)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    camera_handler.start(socketio)
    data_handler.start(socketio)
    # Send initial status
    status = {
        **gpio_handler.get_status(),
        **alarm_handler.get_status()
    }
    socketio.emit('status_update', status)
    socketio.emit('full_dataset', data_handler.get_current_data())

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    camera_handler.stop()
    data_handler.stop()

@socketio.on('toggle_alarm')
def handle_toggle_alarm():
    enabled = alarm_handler.toggle_enable()
    socketio.emit('alarm_status', {'enabled': enabled})

@socketio.on('get_status')
def handle_get_status():
    status = {
        **gpio_handler.get_status(),
        **alarm_handler.get_status()
    }
    socketio.emit('status_update', status)

if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        gpio_handler.cleanup()
        alarm_handler.cleanup()
        data_handler.stop()