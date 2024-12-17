from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from modules.camera import CameraHandler

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

camera_handler = CameraHandler(fps=20)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    camera_handler.start(socketio)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    camera_handler.stop()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)