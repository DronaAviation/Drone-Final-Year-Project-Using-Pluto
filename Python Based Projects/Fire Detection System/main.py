"""
Fire/Smoke Detection with PlutoCam + YOLO

Controls:
  q = quit
  f = flip image 180°
  y = toggle YOLO detection

Usage:
  # PlutoCam (default) — connect to drone WiFi (192.168.0.1) first
  python main.py --yolo-weights best.pt

  # Webcam (for testing without drone)
  python main.py --yolo-weights best.pt --source webcam

  # Video file
  python main.py --yolo-weights best.pt --source path/to/video.mp4

Notes:
  - Uses plutocam package to stream from PlutoCam (IP: 192.168.0.1, stream port: 7060).
  - Works with Ultralytics YOLO (v8+). Accepts .pt (preferred) or .onnx.
  - pip install plutocam plutocontrol ultralytics opencv-python numpy
"""

import argparse
import cv2
import numpy as np
import subprocess
import sys
import threading
import time

# ------------------ CLI ------------------
parser = argparse.ArgumentParser()
parser.add_argument("--source", type=str, default="plutocam",
                    help="Video source: 'plutocam' (default), 'webcam', or path to video file")
parser.add_argument("--yolo-weights", type=str, required=True,
                    help="Path to YOLO fire/smoke weights (.pt/.onnx)")
parser.add_argument("--yolo-conf", type=float, default=0.35,
                    help="YOLO confidence threshold")
parser.add_argument("--yolo-iou", type=float, default=0.5,
                    help="YOLO NMS IoU threshold")
parser.add_argument("--yolo-size", type=int, default=320,
                    help="YOLO inference image size (smaller = faster, default 320)")
parser.add_argument("--skip-frames", type=int, default=2,
                    help="Run YOLO every N frames (default 2, 1=every frame)")
parser.add_argument("--cam-ip", type=str, default="192.168.0.1",
                    help="PlutoCam IP address (default: 192.168.0.1)")
parser.add_argument("--cpu", action="store_true", help="Force CPU for YOLO")
args = parser.parse_args()

ALERT_COOLDOWN = 1.0

print("Controls: 'q'=quit  'f'=flip  'y'=toggle YOLO  'h'=toggle HSV")

flip_image = False
use_yolo = True
use_hsv = True  # HSV fire detection ON by default
last_beep = 0.0
frame_count = 0
last_boxes_overlay = []

# ------------------ YOLO load ------------------
try:
    from ultralytics import YOLO
except ImportError:
    print("[FATAL] ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)

device = "cpu" if args.cpu else None
try:
    model = YOLO(args.yolo_weights)
    CLASS_NAMES = {}
    try:
        CLASS_NAMES = model.model.names if hasattr(model, "model") else {}
    except Exception:
        pass
    print(f"[INFO] YOLO weights loaded: {args.yolo_weights}")
    if CLASS_NAMES:
        print(f"[INFO] Classes: {CLASS_NAMES}")
except Exception as e:
    print(f"[FATAL] Could not load YOLO weights: {e}")
    sys.exit(1)

# Warm up YOLO
print("[INFO] Warming up YOLO model ...")
dummy = np.zeros((args.yolo_size, args.yolo_size, 3), dtype=np.uint8)
model.predict(source=dummy, verbose=False, device=device, imgsz=args.yolo_size)
print("[INFO] YOLO ready")

WANTED_SUBSTR = ("fire", "flame", "smoke")

def class_is_wanted(cidx):
    if not CLASS_NAMES:
        return True
    name = str(CLASS_NAMES.get(cidx, "")).lower()
    return any(s in name for s in WANTED_SUBSTR)

# ------------------ Helpers ------------------
def maybe_beep():
    global last_beep
    now = time.time()
    if (now - last_beep) >= ALERT_COOLDOWN:
        print("\a", end="", flush=True)
        last_beep = now

def draw_detections(frame, detections, y_hits):
    for (x1, y1, x2, y2, label, score, color) in detections:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label} {score:.2f}", (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    if y_hits > 0:
        cv2.putText(frame, "!! FIRE/SMOKE DETECTED !!",
                    (10, 60), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 255), 2)
        maybe_beep()

def run_yolo(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    try:
        results = model.predict(
            source=rgb, verbose=False,
            conf=args.yolo_conf, iou=args.yolo_iou,
            device=device, imgsz=args.yolo_size
        )
    except Exception as e:
        print(f"[YOLO] inference error: {e}")
        return [], 0

    detections = []
    hits = 0
    if results:
        r = results[0]
        boxes = getattr(r, "boxes", None)
        if boxes is not None and boxes.xyxy is not None:
            xyxy = boxes.xyxy.cpu().numpy()
            cls = boxes.cls.cpu().numpy().astype(int) if boxes.cls is not None else np.zeros(len(xyxy), dtype=int)
            confs = boxes.conf.cpu().numpy() if boxes.conf is not None else np.ones(len(xyxy))

            keep_all = True
            if CLASS_NAMES:
                keep_all = not any(class_is_wanted(i) for i in set(cls))

            for i, (x1, y1, x2, y2) in enumerate(xyxy):
                c = cls[i] if i < len(cls) else 0
                if not keep_all and not class_is_wanted(c):
                    continue
                score = confs[i] if i < len(confs) else 1.0
                hits += 1
                label = CLASS_NAMES.get(c, f"id:{c}")
                color = (0, 0, 255) if "fire" in str(label).lower() or "flame" in str(label).lower() else (255, 255, 0)
                detections.append((int(x1), int(y1), int(x2), int(y2), label, score, color))

    return detections, hits


# ------------------ HSV Fire Detection ------------------
# Fire has strong red/orange/yellow colors and high saturation+value
# We use two HSV ranges to catch both red-orange and deep red (wraps around H=0)
HSV_LOWER1 = np.array([0, 120, 150])    # deep red / orange
HSV_UPPER1 = np.array([35, 255, 255])
HSV_LOWER2 = np.array([160, 120, 150])  # wrapping red (near H=180)
HSV_UPPER2 = np.array([180, 255, 255])
HSV_MIN_AREA = 500  # minimum contour area to count as fire (pixels)

def detect_fire_hsv(frame):
    """
    Detect fire-colored regions using HSV color space.
    Returns list of (x1, y1, x2, y2, label, score, color) and hit count.
    Fast — runs every frame.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, HSV_LOWER1, HSV_UPPER1)
    mask2 = cv2.inRange(hsv, HSV_LOWER2, HSV_UPPER2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Clean up noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detections = []
    hits = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < HSV_MIN_AREA:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        # Confidence based on how much of bounding box is fire-colored
        roi_mask = mask[y:y+h, x:x+w]
        fill_ratio = cv2.countNonZero(roi_mask) / (w * h) if w * h > 0 else 0
        if fill_ratio < 0.25:
            continue
        hits += 1
        score = min(fill_ratio * 1.5, 1.0)  # pseudo-confidence
        detections.append((x, y, x + w, y + h, "HSV-Fire", score, (0, 140, 255)))

    return detections, hits


# ============================================================
# PlutoCam frame reader using pylwdrone + ffmpeg decoder
# ============================================================
class PlutoCamReader:
    """
    Reads video from PlutoCam using plutocam/pylwdrone (stream port 7060).
    H264 frames from plutocam → ffmpeg decodes & scales → raw BGR for OpenCV.
    """
    # Fixed output resolution — ffmpeg scales to this regardless of input
    OUT_W = 640
    OUT_H = 480

    def __init__(self, ip="192.168.0.1"):
        self.ip = ip
        self._drone = None
        self._ffmpeg = None
        self._stream_thread = None
        self._running = False
        self._frame = None
        self._frame_lock = threading.Lock()
        self._got_first_frame = threading.Event()
        self._bytes_per_frame = self.OUT_W * self.OUT_H * 3

    def start(self):
        import plutocam
        print(f"[PlutoCam] Connecting to {self.ip} (stream port 7060) ...")
        self._drone = plutocam.LWDrone(ip=self.ip)

        # ffmpeg: decode H264 from stdin → scale to fixed 640x480 → raw BGR out
        self._ffmpeg = subprocess.Popen(
            [
                "ffmpeg",
                "-loglevel", "error",
                "-fflags", "nobuffer",
                "-flags", "low_delay",
                "-probesize", "2048",
                "-analyzeduration", "500000",
                "-f", "h264",
                "-i", "-",
                "-vf", f"scale={self.OUT_W}:{self.OUT_H}",
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._running = True
        self._stream_thread = threading.Thread(target=self._feed_loop, daemon=True)
        self._stream_thread.start()
        self._read_thread = threading.Thread(target=self._decode_loop, daemon=True)
        self._read_thread.start()

        if not self._got_first_frame.wait(timeout=15):
            print("[PlutoCam] WARNING: No frames received in 15s. Check WiFi connection.")
            return False
        print(f"[PlutoCam] Stream started ({self.OUT_W}x{self.OUT_H})")
        return True

    def _feed_loop(self):
        """Feed H264 bytes from plutocam into ffmpeg stdin."""
        try:
            for frame in self._drone.start_video_stream():
                if not self._running:
                    break
                try:
                    self._ffmpeg.stdin.write(frame.frame_bytes)
                    self._ffmpeg.stdin.flush()
                except BrokenPipeError:
                    break
        except Exception as e:
            if self._running:
                print(f"[PlutoCam] Stream error: {e}")
        finally:
            try:
                self._ffmpeg.stdin.close()
            except Exception:
                pass

    def _decode_loop(self):
        """Read decoded BGR frames from ffmpeg stdout."""
        while self._running:
            raw = self._read_exact(self._bytes_per_frame)
            if raw is None:
                break
            frame = np.frombuffer(raw, dtype=np.uint8).reshape(
                (self.OUT_H, self.OUT_W, 3)
            ).copy()
            with self._frame_lock:
                self._frame = frame
            if not self._got_first_frame.is_set():
                self._got_first_frame.set()

    def _read_exact(self, nbytes):
        buf = bytearray()
        while len(buf) < nbytes:
            chunk = self._ffmpeg.stdout.read(nbytes - len(buf))
            if not chunk:
                return None
            buf.extend(chunk)
        return bytes(buf)

    def read(self):
        """OpenCV-compatible read() → (success, frame)"""
        with self._frame_lock:
            if self._frame is not None:
                return True, self._frame.copy()
        return False, None

    def release(self):
        self._running = False
        try:
            if self._ffmpeg and self._ffmpeg.poll() is None:
                self._ffmpeg.terminate()
        except Exception:
            pass

    def isOpened(self):
        return self._running and self._frame is not None


# ------------------ Video Source ------------------
cap = None
plutocam_reader = None

if args.source == "plutocam":
    plutocam_reader = PlutoCamReader(ip=args.cam_ip)
    if not plutocam_reader.start():
        print("[ERROR] PlutoCam failed. Make sure you're on drone WiFi.")
        print("        Use --source webcam to test with webcam instead.")
        sys.exit(1)

elif args.source == "webcam":
    print("[INFO] Opening webcam ...")
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        # Fallback to default backend
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FATAL] Could not open webcam")
        sys.exit(1)
    # Set webcam to 640x480 for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Webcam opened at {w}x{h}")

else:
    print(f"[INFO] Opening video file: {args.source}")
    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        print(f"[FATAL] Could not open video: {args.source}")
        sys.exit(1)
    print("[INFO] Video file opened")

# Unified frame reader
def get_frame():
    if plutocam_reader is not None:
        return plutocam_reader.read()
    return cap.read()

# ------------------ Main Loop ------------------
fps_time = time.time()
fps_count = 0
fps_display = 0.0

try:
    while True:
        ret, frame = get_frame()
        if not ret:
            # For PlutoCam, brief gaps are ok — retry
            if plutocam_reader is not None:
                time.sleep(0.01)
                continue
            print("Warning: No frame received. Exiting loop.")
            break

        if flip_image:
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        all_detections = []
        total_hits = 0

        # YOLO detection (runs every N frames)
        if use_yolo:
            frame_count += 1
            if frame_count % args.skip_frames == 0:
                last_boxes_overlay, _ = run_yolo(frame)
            all_detections.extend(last_boxes_overlay)
            total_hits += len(last_boxes_overlay)

        # HSV fire detection (runs every frame — very fast)
        if use_hsv:
            hsv_dets, hsv_hits = detect_fire_hsv(frame)
            all_detections.extend(hsv_dets)
            total_hits += hsv_hits

        draw_detections(frame, all_detections, total_hits)

        # FPS counter
        fps_count += 1
        now = time.time()
        if now - fps_time >= 1.0:
            fps_display = fps_count / (now - fps_time)
            fps_count = 0
            fps_time = now

        # HUD
        src_label = "PlutoCam" if plutocam_reader else args.source
        y_tag = "ON" if use_yolo else "OFF"
        h_tag = "ON" if use_hsv else "OFF"
        status = f"{src_label} | YOLO:{y_tag} HSV:{h_tag} | hits:{total_hits} | {fps_display:.0f}fps"
        cv2.putText(frame, status, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 255, 50), 2)

        # Resize for display if frame is too large (avoids tearing on macOS)
        display = frame
        if frame.shape[1] > 800:
            scale = 800 / frame.shape[1]
            display = cv2.resize(frame, (800, int(frame.shape[0] * scale)))
        cv2.imshow("Fire Detection - PlutoCam", display)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("f"):
            flip_image = not flip_image
            print("Image flip toggled.")
        elif key == ord("y"):
            use_yolo = not use_yolo
            print(f"YOLO {'enabled' if use_yolo else 'disabled'}.")
        elif key == ord("h"):
            use_hsv = not use_hsv
            print(f"HSV fire detection {'enabled' if use_hsv else 'disabled'}.")

except KeyboardInterrupt:
    print("\nExiting on user interrupt.")
finally:
    cv2.destroyAllWindows()
    if cap is not None:
        cap.release()
    if plutocam_reader is not None:
        plutocam_reader.release()
