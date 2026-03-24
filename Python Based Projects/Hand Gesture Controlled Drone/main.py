import cv2
import mediapipe as mp
import numpy as np
import threading
import time
import os
from collections import deque, Counter
from plutocontrol import Pluto

# ──────────────────────────────────────────────
# Shared state
# ──────────────────────────────────────────────
lock = threading.Lock()
shared = {
    "gesture": "NONE",       # FIST, PALM, OPEN_HAND, NONE
    "hand_x": 0.5,
    "hand_y": 0.5,
    "armed": False,
    "running": True,
    "disarm_progress": 0.0,
    "throttle_target": 1500, # Set by keyboard W/S
    "rc_throttle": 1500,
    "rc_pitch": 1500,
    "rc_roll": 1500,
    "rc_yaw": 1500,
    "drone_connected": False,
}

# ──────────────────────────────────────────────
# Settings
# ──────────────────────────────────────────────
STABILITY_WINDOW = 8
STABILITY_THRESHOLD = 6
FINGER_MARGIN = 0.03
DEAD_ZONE = 0.12
DISARM_HOLD_SECONDS = 2.0  # Hold FIST for 2s to land + disarm

# RC range: 1400 to 1600
RC_MIN = 1300
RC_MAX = 1700
RC_MID = 1500
JOYSTICK_RANGE = 100

# Smoothing: how fast RC values move toward target (0.0=frozen, 1.0=instant)
RC_SMOOTHING = 0.15  # 15% per frame — smooth but responsive

# Throttle step per key press
THROTTLE_STEP = 10  # W/S keys change throttle by ±10 each press

# ──────────────────────────────────────────────
# Hand detection helpers
# ──────────────────────────────────────────────
FINGER_TIPS = [8, 12, 16, 20]
FINGER_PIPS = [6, 10, 14, 18]

def count_fingers(landmarks, handedness):
    count = 0
    if handedness == "Right":
        if landmarks[4].x < landmarks[3].x - FINGER_MARGIN:
            count += 1
    else:
        if landmarks[4].x > landmarks[3].x + FINGER_MARGIN:
            count += 1
    for tip, pip in zip(FINGER_TIPS, FINGER_PIPS):
        if landmarks[tip].y < landmarks[pip].y - FINGER_MARGIN:
            count += 1
    return count

def classify_gesture(fingers):
    if fingers == 0:
        return "FIST"
    elif fingers == 5:
        return "PALM"
    elif fingers == 2:
        return "TWO_FINGERS"
    else:
        return "OPEN_HAND"

def get_hand_center(landmarks):
    palm_indices = [0, 5, 9, 13, 17]
    cx = sum(landmarks[i].x for i in palm_indices) / len(palm_indices)
    cy = sum(landmarks[i].y for i in palm_indices) / len(palm_indices)
    return cx, cy

def hand_to_rc(hand_pos):
    """Hand position (0-1) → RC value (1400-1600). Dead zone → 1500."""
    offset = hand_pos - 0.5
    if abs(offset) < DEAD_ZONE:
        return RC_MID
    if offset > 0:
        scaled = (offset - DEAD_ZONE) / (0.5 - DEAD_ZONE)
    else:
        scaled = (offset + DEAD_ZONE) / (0.5 - DEAD_ZONE)
    rc = RC_MID + int(scaled * JOYSTICK_RANGE)
    return max(RC_MIN, min(RC_MAX, rc))

# ──────────────────────────────────────────────
# Gesture stabilizer
# ──────────────────────────────────────────────
class GestureStabilizer:
    def __init__(self):
        self.history = deque(maxlen=STABILITY_WINDOW)
        self.stable = "NONE"

    def update(self, raw):
        self.history.append(raw)
        if len(self.history) < 3:
            return self.stable
        counts = Counter(self.history)
        best, freq = counts.most_common(1)[0]
        if freq >= STABILITY_THRESHOLD:
            self.stable = best
        return self.stable

    @property
    def confidence(self):
        if not self.history:
            return 0.0
        counts = Counter(self.history)
        _, freq = counts.most_common(1)[0]
        return freq / len(self.history)

# ──────────────────────────────────────────────
# Drone control thread
# ──────────────────────────────────────────────
def smooth(current, target, factor=RC_SMOOTHING):
    """Gradually move current toward target. Returns new value."""
    diff = target - current
    if abs(diff) < 1:
        return target
    return current + diff * factor

def drone_control_thread():
    drone = Pluto()
    drone.connect()

    # Check actual connection status (library doesn't raise, just sets .connected)
    if not drone.connected:
        print("[Drone] NOT CONNECTED - check drone WiFi")
        with lock:
            shared["drone_connected"] = False
        return

    print("[Drone] Connected and verified")
    with lock:
        shared["drone_connected"] = True

    armed = False
    last_action_time = 0

    # Current smooth RC values (start at neutral)
    cur_pitch = float(RC_MID)
    cur_roll = float(RC_MID)
    cur_throttle = float(RC_MID)

    while True:
        with lock:
            if not shared["running"]:
                break
            gesture = shared["gesture"]
            hand_x = shared["hand_x"]
            hand_y = shared["hand_y"]
            disarm_progress = shared["disarm_progress"]
            throttle_target = shared["throttle_target"]

        now = time.time()

        # Target RC values for this frame
        target_pitch = RC_MID
        target_roll = RC_MID

        # ── PALM = Arm (no takeoff yet) ──
        if gesture == "PALM" and not armed:
            if now - last_action_time > 2.0:
                print("[Drone] ARM")
                drone.arm()
                armed = True
                last_action_time = now
                with lock:
                    shared["armed"] = True

        # ── TWO FINGERS = Takeoff (after armed) ──
        elif gesture == "TWO_FINGERS" and armed:
            if now - last_action_time > 2.0:
                print("[Drone] TAKEOFF")
                drone.take_off()
                last_action_time = now

        # ── FIST held 2s = Land + Disarm ──
        elif disarm_progress >= 1.0 and armed:
            if now - last_action_time > 2.0:
                print("[Drone] LAND + DISARM")
                drone.land()
                drone.disarm()
                armed = False
                last_action_time = now
                cur_throttle = float(RC_MID)
                with lock:
                    shared["armed"] = False
                    shared["throttle_target"] = RC_MID

        # ── OPEN HAND = Joystick ──
        elif armed and gesture == "OPEN_HAND":
            target_pitch = hand_to_rc(1.0 - hand_y)  # Hand up = forward
            target_roll = hand_to_rc(hand_x)          # Hand right = roll right

        # Smoothly move toward targets (gradual change)
        cur_pitch = smooth(cur_pitch, target_pitch)
        cur_roll = smooth(cur_roll, target_roll)
        cur_throttle = smooth(cur_throttle, throttle_target)

        # Clamp and send to drone
        rc_pitch = max(RC_MIN, min(RC_MAX, int(cur_pitch)))
        rc_roll = max(RC_MIN, min(RC_MAX, int(cur_roll)))
        rc_throttle = max(RC_MIN, min(RC_MAX, int(cur_throttle)))

        if armed:
            drone.rcPitch = rc_pitch
            drone.rcRoll = rc_roll
            drone.rcThrottle = rc_throttle

        # Check connection is still alive
        with lock:
            shared["drone_connected"] = drone.connected

        # Read RC values for display
        try:
            rc_vals = drone.rc_values()
            with lock:
                shared["rc_roll"] = rc_vals[0]
                shared["rc_pitch"] = rc_vals[1]
                shared["rc_throttle"] = rc_vals[2]
                shared["rc_yaw"] = rc_vals[3]
        except Exception:
            with lock:
                shared["rc_pitch"] = rc_pitch
                shared["rc_roll"] = rc_roll
                shared["rc_throttle"] = rc_throttle

        time.sleep(0.1)

    if armed:
        print("[Drone] Emergency land on exit")
        drone.land()
        drone.disarm()
    drone.disconnect()
    with lock:
        shared["drone_connected"] = False
    print("[Drone] Disconnected")

# ──────────────────────────────────────────────
# Drawing
# ──────────────────────────────────────────────
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),(0,17),
]

def text(frame, txt, pos, scale, color, thick=2):
    cv2.putText(frame, txt, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thick + 3)
    cv2.putText(frame, txt, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick)

def draw_hand(frame, result):
    if not result.hand_landmarks:
        return
    h, w, _ = frame.shape
    for lms in result.hand_landmarks:
        for s, e in HAND_CONNECTIONS:
            cv2.line(frame, (int(lms[s].x*w), int(lms[s].y*h)),
                     (int(lms[e].x*w), int(lms[e].y*h)), (0, 255, 0), 2)
        for lm in lms:
            cv2.circle(frame, (int(lm.x*w), int(lm.y*h)), 4, (0, 0, 255), -1)

def draw_joystick(frame, hand_x, hand_y, is_armed):
    h, w, _ = frame.shape
    cx, cy = w // 2, h // 2
    dz_w, dz_h = int(DEAD_ZONE * w), int(DEAD_ZONE * h)

    # Dead zone box
    overlay = frame.copy()
    cv2.rectangle(overlay, (cx-dz_w, cy-dz_h), (cx+dz_w, cy+dz_h), (80, 80, 80), -1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
    cv2.rectangle(frame, (cx-dz_w, cy-dz_h), (cx+dz_w, cy+dz_h), (150, 150, 150), 2)

    # Crosshair
    cv2.line(frame, (cx, 120), (cx, h), (100, 100, 100), 1)
    cv2.line(frame, (0, cy), (w, cy), (100, 100, 100), 1)

    # Labels
    text(frame, "FORWARD", (cx-55, 145), 0.7, (0, 0, 255), 2)
    text(frame, "BACKWARD", (cx-65, h-20), 0.7, (0, 0, 255), 2)
    text(frame, "LEFT", (15, cy-10), 0.7, (0, 0, 255), 2)
    text(frame, "RIGHT", (w-90, cy-10), 0.7, (0, 0, 255), 2)

    # Hand dot
    if is_armed and 0 < hand_x < 1 and 0 < hand_y < 1:
        hx, hy = int(hand_x * w), int(hand_y * h)
        cv2.line(frame, (cx, cy), (hx, hy), (0, 255, 255), 2)
        cv2.circle(frame, (hx, hy), 12, (0, 255, 255), -1)
        cv2.circle(frame, (hx, hy), 14, (255, 255, 255), 2)

    cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)

def draw_rc_panel(frame, thr, pit, rol, yaw):
    h, w, _ = frame.shape
    px, py = w - 220, 120
    pw, ph = 210, 175

    overlay = frame.copy()
    cv2.rectangle(overlay, (px, py), (px+pw, py+ph), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.rectangle(frame, (px, py), (px+pw, py+ph), (0, 200, 255), 2)
    text(frame, "RC VALUES", (px+45, py+25), 0.6, (0, 200, 255), 2)

    channels = [("THR", thr, (0,255,255)), ("PIT", pit, (0,255,0)),
                ("ROL", rol, (255,200,0)), ("YAW", yaw, (255,0,255))]
    for i, (name, val, color) in enumerate(channels):
        y = py + 50 + i * 32
        text(frame, name, (px+5, y+5), 0.45, color, 1)
        text(frame, str(val), (px+155, y+5), 0.45, (255,255,255), 1)
        bx = px + 50
        bw = 100
        cv2.rectangle(frame, (bx, y-8), (bx+bw, y+5), (50,50,50), -1)
        cv2.line(frame, (bx+bw//2, y-8), (bx+bw//2, y+5), (150,150,150), 1)
        fill = int(((val - RC_MID) / 100) * (bw // 2))
        mid = bx + bw // 2
        if fill > 0:
            cv2.rectangle(frame, (mid, y-8), (mid+fill, y+5), color, -1)
        elif fill < 0:
            cv2.rectangle(frame, (mid+fill, y-8), (mid, y+5), color, -1)

def draw_disarm_timer(frame, progress):
    h, w, _ = frame.shape
    cx, cy = w // 2, h // 2
    radius = 60
    overlay = frame.copy()
    cv2.circle(overlay, (cx, cy), radius+5, (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
    angle = int(progress * 360)
    color = (0, 0, 255) if progress < 1.0 else (0, 255, 0)
    cv2.ellipse(frame, (cx, cy), (radius, radius), -90, 0, angle, color, 8)
    remaining = DISARM_HOLD_SECONDS * (1.0 - progress)
    text(frame, f"{remaining:.1f}s", (cx-25, cy-10), 0.8, (255, 255, 255), 2)
    text(frame, "DISARM", (cx-40, cy+20), 0.6, (0, 0, 255), 2)

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        print("Download: curl -L -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task")
        return

    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        min_tracking_confidence=0.7,
    )
    landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
    stabilizer = GestureStabilizer()

    drone_thread = threading.Thread(target=drone_control_thread, daemon=True)
    drone_thread.start()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        with lock:
            shared["running"] = False
        return

    print("Hand Gesture Drone Control")
    print("==========================")
    print("PALM         = Arm")
    print("2 FINGERS    = Takeoff (after armed)")
    print("FIST (2s)    = Land + Disarm")
    print("OPEN HAND    = Joystick (move hand to fly)")
    print("NO HAND      = Hover")
    print("")
    print("KEYBOARD:")
    print("  W = Throttle UP    (+10)")
    print("  S = Throttle DOWN  (-10)")
    print("  R = Reset throttle (1500)")
    print("  Q = Quit")
    print()

    start_time = time.time()
    fist_start_time = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int((time.time() - start_time) * 1000)
        results = landmarker.detect_for_video(mp_image, ts)

        raw_gesture = "NONE"
        hand_x, hand_y = 0.5, 0.5

        if results.hand_landmarks and results.handedness:
            lms = results.hand_landmarks[0]
            hand = results.handedness[0][0].category_name
            draw_hand(frame, results)
            fingers = count_fingers(lms, hand)
            raw_gesture = classify_gesture(fingers)
            hand_x, hand_y = get_hand_center(lms)

        stable = stabilizer.update(raw_gesture)

        # Disarm safety lock — FIST held for 2s
        disarm_progress = 0.0
        with lock:
            is_armed = shared["armed"]
        if stable == "FIST" and is_armed:
            if fist_start_time is None:
                fist_start_time = time.time()
            disarm_progress = min((time.time() - fist_start_time) / DISARM_HOLD_SECONDS, 1.0)
        else:
            fist_start_time = None

        with lock:
            shared["gesture"] = stable
            shared["hand_x"] = hand_x
            shared["hand_y"] = hand_y
            shared["disarm_progress"] = disarm_progress
            is_armed = shared["armed"]
            rc_t = shared["rc_throttle"]
            rc_p = shared["rc_pitch"]
            rc_r = shared["rc_roll"]
            rc_y = shared["rc_yaw"]

        # ── Draw overlays ──
        draw_joystick(frame, hand_x, hand_y, is_armed)
        draw_rc_panel(frame, rc_t, rc_p, rc_r, rc_y)

        # ── Top HUD ──
        cv2.rectangle(frame, (0, 0), (w, 118), (0, 0, 0), -1)

        # Gesture
        if stable == "OPEN_HAND" and is_armed:
            gesture_text = "JOYSTICK"
        elif stable == "FIST" and is_armed:
            gesture_text = f"DISARMING... {disarm_progress:.0%}"
        elif stable == "PALM" and not is_armed:
            gesture_text = "PALM -> ARM"
        elif stable == "TWO_FINGERS" and is_armed:
            gesture_text = "2 FINGERS -> TAKEOFF"
        else:
            gesture_text = stable
        text(frame, gesture_text, (10, 32), 0.9, (0, 255, 255), 2)

        # Confidence
        conf = stabilizer.confidence
        cc = (0,255,0) if conf >= 0.75 else (0,165,255) if conf >= 0.5 else (0,0,255)
        cv2.rectangle(frame, (10, 48), (10+int(conf*200), 63), cc, -1)
        cv2.rectangle(frame, (10, 48), (210, 63), (200,200,200), 2)
        text(frame, f"{conf:.0%}", (220, 62), 0.5, (255,255,255), 1)

        # RC summary + throttle target
        with lock:
            thr_target = shared["throttle_target"]
        text(frame, f"T:{rc_t}  P:{rc_p}  R:{rc_r}  Y:{rc_y}",
             (10, 85), 0.55, (255, 255, 0), 2)
        text(frame, f"Throttle Target: {thr_target}  [W=Up S=Down R=Reset]",
             (10, 105), 0.45, (0, 255, 255), 1)

        # Armed status
        st = "ARMED" if is_armed else "DISARMED"
        sc = (0, 0, 255) if is_armed else (100, 100, 100)
        text(frame, st, (w-200, 32), 0.9, sc, 3)

        # Drone connection status
        with lock:
            connected = shared["drone_connected"]
        if connected:
            text(frame, "DRONE: CONNECTED", (w-250, 60), 0.5, (0, 255, 0), 2)
        else:
            text(frame, "DRONE: NOT CONNECTED", (w-280, 60), 0.5, (0, 0, 255), 2)

        # Disarm countdown
        if is_armed and disarm_progress > 0:
            draw_disarm_timer(frame, disarm_progress)

        cv2.imshow("Hand Gesture Drone Control", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("w"):
            with lock:
                shared["throttle_target"] = min(RC_MAX, shared["throttle_target"] + THROTTLE_STEP)
                print(f"[Throttle] UP -> {shared['throttle_target']}")
        elif key == ord("s"):
            with lock:
                shared["throttle_target"] = max(RC_MIN, shared["throttle_target"] - THROTTLE_STEP)
                print(f"[Throttle] DOWN -> {shared['throttle_target']}")
        elif key == ord("r"):
            with lock:
                shared["throttle_target"] = RC_MID
                print("[Throttle] RESET -> 1500")

    landmarker.close()
    with lock:
        shared["running"] = False
    drone_thread.join(timeout=5)
    cap.release()
    cv2.destroyAllWindows()
    print("Exited cleanly")

if __name__ == "__main__":
    main()
