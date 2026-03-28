# Fire Detection System (Python + OpenCV + PlutoCam)

## Project Idea

Use the Pluto drone with **PlutoCam** to detect **fire or flames** in real-time using computer vision, and trigger alerts — building an aerial fire surveillance system.

---

## Objective

Build a **drone-based fire detection and alert system** that flies over an area, processes the camera feed to detect fire/flames, and raises an alarm when fire is detected.

---

## How It Works

1. Pluto drone flies (manually or on a predefined path)
2. PlutoCam streams video to the laptop over WiFi (IP: `192.168.0.1`, stream port: `7060`)
3. Each frame is analyzed using **dual detection**:
   - **HSV color detection** — detects fire-colored regions (red/orange/yellow) every frame (fast)
   - **YOLOv8 model** — detects fire and smoke with bounding boxes and confidence scores (runs every N frames)
4. If fire/smoke is detected, the system triggers a sound alert and highlights the region with bounding boxes
5. A live HUD overlay shows detection status, hit count, and FPS

---

## Architecture

```
PlutoCam Feed                Processing Engine              Alert System
┌────────────────────┐      ┌────────────────────────┐     ┌──────────────────┐
│ WiFi Video Stream  │─────>│ HSV Fire Detection     │────>│ Sound Alert      │
│ (plutocam package) │      │ YOLOv8 Fire/Smoke Model│     │ On-Screen Warning│
│                    │      │ Bounding Box Overlay   │     │                  │
└────────────────────┘      └────────────────────────┘     └──────────────────┘
```

---

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install plutocam plutocontrol ultralytics opencv-python numpy
```

### 3. Install ffmpeg (required for PlutoCam stream decoding)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 4. Download YOLO fire detection weights

Download a YOLOv8 fire/smoke model (`.pt` file) and place it in this folder. Example source:
- [Abonia1/YOLOv8-Fire-and-Smoke-Detection](https://github.com/Abonia1/YOLOv8-Fire-and-Smoke-Detection) — trained weights at `runs/detect/train/weights/best.pt`

---

## How to Run

### PlutoCam (default) — connect to drone WiFi first

```bash
python main.py --yolo-weights fire_best.pt
```

### Webcam (for testing without drone)

```bash
python main.py --yolo-weights fire_best.pt --source webcam
```

### Video file

```bash
python main.py --yolo-weights fire_best.pt --source path/to/video.mp4
```

### All options

```bash
python main.py --help
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--source` | `plutocam` | Video source: `plutocam`, `webcam`, or file path |
| `--yolo-weights` | *(required)* | Path to YOLO `.pt` weights file |
| `--yolo-conf` | `0.35` | YOLO confidence threshold |
| `--yolo-size` | `320` | YOLO inference size (smaller = faster) |
| `--skip-frames` | `2` | Run YOLO every N frames (1 = every frame) |
| `--cam-ip` | `192.168.0.1` | PlutoCam IP address |
| `--cpu` | `false` | Force CPU for YOLO inference |

---

## Controls (while running)

| Key | Action |
|-----|--------|
| `q` | Quit |
| `f` | Flip image 180° |
| `y` | Toggle YOLO detection on/off |
| `h` | Toggle HSV fire detection on/off |

---

## Detection Methods

### HSV Color Detection
- Converts each frame to HSV color space
- Filters for fire colors (red, orange, yellow hues) using two HSV ranges
- Applies morphological cleanup to reduce noise
- Finds contours and filters by area and fill ratio
- Runs every frame (very fast)
- Shown with **orange** bounding boxes labeled `HSV-Fire`

### YOLOv8 Model Detection
- Uses a pre-trained YOLOv8 model for fire and smoke detection
- Provides class labels (`Fire`, `smoke`) with confidence scores
- Runs every N frames (configurable with `--skip-frames`)
- Shown with **red** (fire) or **yellow** (smoke) bounding boxes

Both methods run simultaneously for maximum detection reliability.

---

## Hardware Used

* Pluto X / Pluto 1.2 Drone
* PlutoCam (Pluto camera module)
* Laptop (Python environment)
* Fire source for testing (use candle or fire video for safety)

---

## Guidelines to Build This

1. **Access the PlutoCam feed** — Use OpenCV's `VideoCapture` with PlutoCam's WiFi stream URL
2. **Choose a fire detection method**:
   - **Color-based detection** (simplest):
     - Convert frame to HSV color space
     - Filter for fire-like colors (red, orange, yellow hues)
     - Apply morphological operations to clean up the mask
     - Find contours and check area threshold
   - **CNN-based detection** (more robust):
     - Train a binary classifier (fire vs. no-fire) using a fire dataset
     - Use a lightweight model like MobileNet for real-time inference
   - **YOLO-based detection** (most accurate):
     - Use a pre-trained fire detection YOLO model
     - Provides bounding boxes with confidence scores
3. **Set detection thresholds** — Avoid false positives from red/orange objects; combine color + motion + flicker detection
4. **Build an alert system**:
   - Play an alarm sound using `playsound` or `pygame`
   - Save screenshots with timestamps
   - Log detection events to a CSV file
   - Optionally send email/SMS alerts
5. **Add HUD overlay** — Display detection status, confidence score, and bounding boxes on the video feed
6. **Run a drone control thread** — Use a separate thread that continuously sends flight commands via `plutocontrol` at ~10Hz. The drone can be manually piloted while the detection runs, or you can implement autonomous flight by sending predefined movement commands for surveying an area
7. **Apply frame stabilization** — The drone's movement and motor vibration cause shaky footage; use software-based stabilization (feature matching between consecutive frames) to improve detection accuracy
8. **Integrate drone behavior (optional)** — On fire detection, send commands to hold position over the zone or return to a safe location

---

## Key Challenges to Solve

* **Frame stabilization** — The drone's movement and motor vibration cause camera shake; apply software-based stabilization and run detection on stabilized frames for better accuracy
* **Temporal filtering** — The drone's own movement can cause color shifts and blur that may trigger false fire detections; require fire detection in multiple consecutive frames before raising an alert
* **False positives** — Red/orange objects, sunlight reflections, and warm-colored surfaces can trigger false alarms; combine color + motion + flicker detection for reliability
* **Real-time processing** — Keep detection fast enough for live video; optimize model size and frame resolution
* **Continuous flight control** — The Pluto drone requires a constant stream of commands to stay in flight; ensure your drone control thread keeps running alongside the detection pipeline
* **Testing safely** — Use recorded fire videos or a small controlled candle for testing; never create dangerous fire conditions
* **Distance estimation** — Fire at different distances appears different; consider multi-scale detection

---

## Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)
* [PlutoCam](https://dronaaviation.com/store/)

---

## Future Scope

* Add temperature sensor (IR) for combined visual + thermal detection
* Implement autonomous patrol routes for area surveillance
* Send GPS coordinates of detected fire (with external GPS module)
* Build a web dashboard for remote monitoring
* Multi-drone coordinated surveillance system
