# 🔥 Fire Detection System

A real-time fire detection system built with Python Flask and React, designed to run on a Raspberry Pi. This system uses computer vision to detect fires and triggers an alarm when necessary.

## ⚡ Features

- 📹 Real-time camera feed
- 🤖 AI-powered fire detection using YOLOv5
- ⚠️ Automatic alarm system
- 📊 Real-time data visualization
- 🎛️ Manual alarm control interface

## 🛠️ Prerequisites

- Raspberry Pi (3B+ or newer recommended)
- USB Webcam or Raspberry Pi Camera Module
- Python 3.10 or newer
- Node.js 16.0 or newer
- Conda package manager
- GPIO-connected alarm system

## 🚀 Installation

### Backend Setup

1. Clone the repository:
```bash
git clone [your-repo-url]
cd fire-detection-system
```

2. Create and activate Conda environment:
```bash
cd server
conda create --prefix ./env python=3.10
conda activate ./env
```

3. Install Python dependencies:
```bash
pip install flask flask-socketio flask-cors opencv-python numpy
conda install pytorch torchvision -c pytorch
pip install ultralytics
```

4. On Raspberry Pi, install GPIO:
```bash
sudo apt-get update
sudo apt-get install python3-rpi.gpio
# or
pip install RPi.GPIO
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
```

## 🏃‍♂️ Running the Application

### Start the Backend:
```bash
cd server
conda activate ./env
python app.py
```

### Start the Frontend:
```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:3000`

## 📐 System Architecture

```
Backend (Flask)                 Frontend (React)
┌──────────────┐               ┌──────────────┐
│ Camera Feed  │ ─WebSocket─── │    Video     │
│ AI Model     │               │   Display    │
│ GPIO Control │               │             │
└──────────────┘               └──────────────┘
```

## 🔌 Hardware Setup

1. Connect your USB camera or configure the Raspberry Pi camera module
2. Wire the alarm system to GPIO pins (detailed wiring diagram coming soon)
3. Ensure all connections are secure and properly insulated

## 👥 Contributing

Feel free to open issues and pull requests!

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Safety Disclaimer

This system is designed as a supplementary safety measure and should not be relied upon as the sole fire detection system. Always ensure you have proper smoke detectors and fire safety equipment installed according to local regulations.

## 🤝 Support

For support, please open an issue in the repository or contact [your-contact-info].

## 🙏 Acknowledgments

- YOLOv5 by Ultralytics
- OpenCV community
- React and Flask communities