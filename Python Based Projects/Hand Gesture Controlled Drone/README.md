# Hand Gesture Controlled Drone (Python + OpenCV + MediaPipe)

## Project Idea

Control the Pluto drone using **real-time hand gestures** detected via a webcam, using OpenCV and MediaPipe for hand tracking.

---

## Objective

Enable **gesture-based flight control** of the drone without any physical controller — the pilot uses hand signs in front of a laptop camera to fly the drone.

---

## How It Works

1. Webcam captures video frames (Main Thread)
2. MediaPipe detects hand landmarks and counts extended fingers
3. Finger count is mapped to a drone command
4. A separate Drone Control Thread reads the gesture and sends commands to Pluto via `plutocontrol`
5. Two threads ensure smooth camera feed while drone commands are sent continuously

---

## Architecture

```
Main Thread                         Drone Thread
┌──────────────────────┐           ┌──────────────────────┐
│ OpenCV Camera Feed   │  shared   │ Read gesture state   │
│ MediaPipe Detection  │──state───>│ Send plutocontrol    │
│ HUD Overlay Display  │  (lock)   │ commands @ 10Hz      │
└──────────────────────┘           └──────────────────────┘
```

---

## Gesture Controls

| Fingers | Gesture     | Drone Action |
|---------|-------------|--------------|
| 5       | Open Palm   | Arm + Takeoff |
| 0       | Fist        | Land + Disarm |
| 1       | Index Up    | Forward (Pitch) |
| 2       | Peace / V   | Backward (Pitch) |
| 3       | Three Up    | Roll Left |
| 4       | Four Up     | Roll Right |

---

## Requirements

Install required Python packages:

```bash
pip install opencv-python mediapipe plutocontrol
```

---

## How to Run

1. Connect your laptop to the Pluto drone WiFi
2. Run the script:

```bash
python main.py
```

3. Show hand gestures to the webcam to control the drone
4. Press **Q** to quit (drone will land safely)

---

## Hardware Used

* Pluto X / Pluto 1.2 Drone
* Laptop with webcam (Python environment)

---

## Key Features

* **Two-threaded design** — smooth camera feed + continuous drone commands
* **Debounced arm/disarm** — prevents accidental takeoff or landing
* **HUD overlay** — shows gesture name, finger count, and drone armed status
* **Safe exit** — auto-lands drone on quit

---

## Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)

---

## Future Scope

* Add more gestures (yaw, height control)
* Use hand position in frame for proportional control
* Add voice feedback using text-to-speech
* Combine with face tracking for autonomous follow mode
