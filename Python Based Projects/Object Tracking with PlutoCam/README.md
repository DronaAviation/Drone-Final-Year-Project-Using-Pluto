# Object Tracking with PlutoCam (Python + OpenCV)

## Project Idea

Use the **PlutoCam** (Pluto drone's onboard camera) to detect and **track a specific object** in real-time, adjusting the drone's position to keep the object centered in the frame.

---

## Objective

Build an **autonomous object-following drone** that uses computer vision to detect a target object and sends flight corrections to keep the object in the center of the camera feed.

---

## How It Works

1. PlutoCam streams video to the laptop over WiFi
2. OpenCV processes each frame to detect the target object
3. Object's position in the frame is compared to the center
4. Position error is converted into drone movement commands (pitch, roll, yaw)
5. Commands are sent to Pluto via `plutocontrol` to adjust position
6. Loop continues, creating a real-time tracking system

---

## Architecture

```
Video Stream Thread              Processing Thread              Drone Thread
┌────────────────────┐          ┌────────────────────┐         ┌──────────────────┐
│ PlutoCam WiFi Feed │─frames──>│ Object Detection   │─error──>│ PID Controller   │
│ Frame Capture      │          │ Position Tracking  │  data   │ Command Mapping  │
│                    │          │ Error Calculation  │         │ plutocontrol Send│
└────────────────────┘          └────────────────────┘         └──────────────────┘
```

---

## Guidelines to Build This

1. **Access the PlutoCam feed** — PlutoCam streams video over WiFi; use OpenCV's `VideoCapture` with the camera's IP stream URL
2. **Choose an object detection method**:
   - **Color-based tracking** (easiest) — Use HSV color filtering to track a colored object (e.g., a red ball)
   - **Contour detection** — Detect shapes and track the largest contour
   - **Template matching** — Track a specific object using a reference image
   - **Deep learning** — Use YOLO or MobileNet SSD for robust object detection
3. **Calculate position error** — Find the difference between the object's center and the frame's center (x-offset, y-offset)
4. **Implement a PID controller** — Use proportional-integral-derivative control to smoothly adjust drone movement based on error. The PID loop must run **continuously at ~10–20Hz**, as the Pluto drone requires a constant stream of commands to maintain flight
5. **Map corrections to drone commands**:
   - Object too far left → Roll left
   - Object too far right → Roll right
   - Object too high → Increase throttle
   - Object too low → Decrease throttle
   - Object too small (far away) → Pitch forward
   - Object too large (too close) → Pitch backward
6. **Add safety bounds** — Limit maximum speed corrections to prevent aggressive movements; keep the dead zone small for responsive tracking
7. **Integrate with `plutocontrol`** — Send the computed corrections as flight commands, including throttle for altitude control. The drone expects continuous commands, so your control loop should never pause or stop sending while in flight

---

## Requirements

Suggested Python packages:

```bash
pip install plutocontrol opencv-python numpy
# For deep learning based detection:
pip install ultralytics  # YOLO
```

---

## How to Run

1. Connect your laptop to the Pluto drone WiFi
2. Ensure PlutoCam is attached and streaming
3. Run your script:

```bash
python main.py
```

4. Place the target object in front of the drone
5. The drone should follow the object autonomously
6. Press **Q** to quit (drone will land safely)

---

## Hardware Used

* Pluto X / Pluto 1.2 Drone
* PlutoCam (Pluto camera module)
* Laptop (Python environment)
* A colored object to track (e.g., a red/green ball)

---

## Key Challenges to Solve

* **Continuous corrections** — The Pluto drone requires constant command input to stay airborne; your PID loop should keep running and sending corrections even when the object is centered, to maintain stable flight
* **Stream latency** — WiFi video stream has delay; account for this lag in your PID tuning and use a derivative term to predict movement
* **PID tuning** — Start with very small proportional gains and increase gradually; aggressive values cause oscillation. Tune one axis at a time (e.g., roll first, then pitch, then throttle)
* **Object loss** — If the object leaves the frame, keep sending neutral flight commands while implementing a search pattern (slow yaw rotation) to re-acquire the object
* **Lighting conditions** — Color-based detection is sensitive to lighting; use HSV instead of RGB
* **Frame rate** — Keep processing fast enough for real-time control; slow processing means less responsive tracking

---

## Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)
* [PlutoCam](https://dronaaviation.com/store/)

---

## Future Scope

* Track faces instead of objects for a follow-me drone
* Add multi-object tracking and priority selection
* Implement gesture-based target selection
* Add altitude hold using object size estimation
* Record tracked footage with overlay annotations
