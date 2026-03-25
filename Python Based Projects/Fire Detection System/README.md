# Fire Detection System (Python + OpenCV + PlutoCam)

## Project Idea

Use the Pluto drone with **PlutoCam** to detect **fire or flames** in real-time using computer vision, and trigger alerts — building an aerial fire surveillance system.

---

## Objective

Build a **drone-based fire detection and alert system** that flies over an area, processes the camera feed to detect fire/flames, and raises an alarm when fire is detected.

---

## How It Works

1. Pluto drone flies (manually or on a predefined path)
2. PlutoCam streams video to the laptop over WiFi
3. Each frame is analyzed for fire-like regions using color detection or a trained model
4. If fire is detected, the system triggers an alert (sound, log, or notification)
5. Fire location is highlighted on the video feed with bounding boxes
6. Optionally, the drone can hover over the fire zone for continuous monitoring

---

## Architecture

```
PlutoCam Feed                Processing Engine              Alert System
┌────────────────────┐      ┌────────────────────────┐     ┌──────────────────┐
│ WiFi Video Stream  │─────>│ Fire Detection Model   │────>│ Sound Alert      │
│ Frame Capture      │      │ (Color / CNN / YOLO)   │     │ Log to File      │
│                    │      │ Bounding Box Overlay   │     │ Screenshot Save  │
└────────────────────┘      └────────────────────────┘     └──────────────────┘
                                      │
                                      v
                            ┌────────────────────────┐
                            │ Drone Control (optional)│
                            │ Hover / Return Home     │
                            └────────────────────────┘
```

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

## Requirements

Suggested Python packages:

```bash
pip install plutocontrol opencv-python numpy
# For CNN approach:
pip install tensorflow keras
# For YOLO approach:
pip install ultralytics
# For alerts:
pip install playsound
```

---

## How to Run

1. Connect your laptop to the Pluto drone WiFi
2. Ensure PlutoCam is attached and streaming
3. Run your script:

```bash
python main.py
```

4. Fly the drone over the area to survey (or use a test video)
5. When fire is detected, the system will alert and highlight on screen
6. Press **Q** to quit

---

## Hardware Used

* Pluto X / Pluto 1.2 Drone
* PlutoCam (Pluto camera module)
* Laptop (Python environment)
* Fire source for testing (use candle or fire video for safety)

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
* Add smoke detection alongside fire detection
* Multi-drone coordinated surveillance system
