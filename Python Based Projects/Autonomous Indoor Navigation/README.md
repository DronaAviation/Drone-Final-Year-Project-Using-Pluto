# Autonomous Indoor Navigation (Python + OpenCV + PlutoCam + ArUco)

## Project Idea

Enable the Pluto drone to **navigate indoors autonomously** using **PlutoCam** and **ArUco markers** as visual waypoints — the drone detects markers placed in the environment, navigates between them, and can hover or land precisely on a target marker.

---

## Objective

Build a **marker-guided autonomous indoor drone** that uses PlutoCam with OpenCV to detect ArUco tags, estimate its position relative to them, and fly between waypoints without manual pilot input using `plutocontrol`.

---

## How It Works

1. ArUco markers are placed at known positions in the indoor environment (walls, floor, ceiling)
2. Drone takes off and PlutoCam begins streaming video to the laptop
3. OpenCV detects ArUco markers in each frame and estimates pose (distance + orientation)
4. Based on which marker is detected and its relative position, the drone decides its next movement
5. Commands are sent to Pluto via `plutocontrol` to navigate toward the next waypoint marker
6. When the final target marker is reached, the drone hovers over it or performs a precision landing

---

## Architecture

```
PlutoCam Feed                 ArUco Processing               Drone Control
┌────────────────────┐       ┌─────────────────────────┐    ┌──────────────────┐
│ WiFi Video Stream  │──────>│ ArUco Detection         │───>│ PID Controller   │
│ Frame Capture      │       │ Pose Estimation         │    │ Command Mapping  │
│                    │       │ Waypoint Decision       │    │ plutocontrol     │
└────────────────────┘       └─────────────────────────┘    └──────────────────┘
                                       │
                                       v
                             ┌─────────────────────────┐
                             │ Navigation State Machine │
                             │ (Takeoff / Search /      │
                             │  Navigate / Hover / Land)│
                             └─────────────────────────┘
```

---

## ArUco Marker Setup

| Marker ID | Placement        | Purpose                    |
|-----------|------------------|----------------------------|
| 0         | Takeoff pad      | Home / start position      |
| 1         | Wall / doorway   | Waypoint 1 — first target  |
| 2         | Wall / corridor  | Waypoint 2 — second target |
| 3         | Ceiling / wall   | Altitude reference         |
| 4         | Floor / landing  | Final target — land here   |

> Print ArUco markers using OpenCV's built-in generator or online ArUco generators. Use `DICT_4X4_50` or `DICT_6X6_250` dictionary.

---

## Guidelines to Build This

1. **Set up PlutoCam feed** — Use OpenCV's `VideoCapture` with PlutoCam's WiFi stream URL to capture frames
2. **ArUco marker detection**:
   - Use `cv2.aruco` module to detect markers in each frame
   - Choose an ArUco dictionary (e.g., `DICT_4X4_50` for small markers)
   - `detectMarkers()` returns marker corners and IDs
3. **Pose estimation**:
   - Use `cv2.aruco.estimatePoseSingleMarkers()` to get rotation and translation vectors
   - This tells you how far and at what angle the drone is from each marker
   - Calibrate PlutoCam first using a checkerboard pattern for accurate pose estimation
4. **Build a navigation state machine**:
   - `TAKEOFF` — Arm and take off to a safe altitude using `plutocontrol`
   - `SEARCH` — Rotate/scan to find the next target marker
   - `NAVIGATE` — Move toward the detected marker, using pose data to correct course
   - `HOVER` — Marker reached; hold position over it
   - `LAND` — Final marker detected; perform precision landing
5. **Implement PID-based corrections**:
   - Use the marker's x-offset from frame center for roll correction
   - Use the marker's y-offset from frame center for throttle correction
   - Use the estimated distance (z from pose) for pitch correction
   - Tune PID gains carefully — start with small values
   - The PID loop must run **continuously at ~10–20Hz**, as the Pluto drone requires a constant stream of commands to maintain stable flight. The ArUco marker feedback serves as the primary source of position correction
6. **Define waypoint sequence** — Create a list of marker IDs in order (e.g., `[0, 1, 2, 4]`); the drone navigates to each in sequence
7. **Add safety mechanisms**:
   - If no marker is detected for N seconds, send neutral commands to maintain altitude and slowly rotate to search
   - Emergency land on timeout or low confidence
   - Maximum altitude and speed limits via `plutocontrol`
   - Always keep the command loop running — the drone needs continuous input to stay airborne
8. **Camera calibration** — Use `cv2.calibrateCamera()` with a checkerboard to get camera matrix and distortion coefficients for accurate pose estimation

---

## Requirements

Suggested Python packages:

```bash
pip install plutocontrol opencv-python opencv-contrib-python numpy
```

> `opencv-contrib-python` is needed for the `cv2.aruco` module.

---

## How to Run

1. Print ArUco markers and place them in your indoor environment
2. Calibrate PlutoCam using a checkerboard (one-time step, save calibration data)
3. Connect your laptop to the Pluto drone WiFi
4. Ensure PlutoCam is attached and streaming
5. Run your script:

```bash
python main.py
```

6. The drone will take off, detect markers, and navigate between waypoints
7. Press **Q** or **Ctrl+C** to trigger emergency landing

---

## Hardware Used

* Pluto X / Pluto 1.2 Drone
* PlutoCam (Pluto camera module)
* Laptop (Python environment)
* Printed ArUco markers (A4 paper)
* Indoor space with markers placed at waypoints

---

## Key Challenges to Solve

* **Camera calibration** — Accurate pose estimation requires proper calibration of PlutoCam; use a checkerboard pattern and save the calibration matrix
* **Marker detection range** — Small markers are hard to detect from far away; use larger printed markers or higher resolution
* **Pose estimation accuracy** — Noisy at large distances or steep angles; add filtering (moving average or Kalman filter) to smooth out pose data
* **WiFi stream latency** — Delay between real-world and processed frame; add safety margins in your control logic
* **PID tuning** — Start with very small gains; test one axis at a time (e.g., only roll correction first). The continuous marker-based feedback loop is essential for keeping the drone on course
* **Marker occlusion** — Handle cases where markers are partially blocked; keep sending the last known correction commands while searching for the marker again
* **Continuous command loop** — The Pluto drone requires commands to be sent at a constant rate to maintain flight; your control thread should never stop sending, even between waypoints

---

## Purchase Links

* [Pluto X Drone Kit](https://dronaaviation.com/store/)

---

## Future Scope

* Add SLAM for building a map while navigating
* Implement return-to-home using Marker ID 0
* Use QR codes alongside ArUco for richer waypoint data (e.g., altitude, speed)
* Multi-drone coordination using shared marker maps
* Combine with obstacle avoidance using computer vision alongside ArUco navigation
* Add a web dashboard showing drone position on a floor plan
