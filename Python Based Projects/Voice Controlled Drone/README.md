# Voice Controlled Drone (Python + Speech Recognition)

## Project Idea

Control the Pluto drone using **voice commands** — speak into your laptop microphone and the drone responds with the corresponding flight action.

---

## Objective

Enable **hands-free flight control** of the drone using natural voice commands, demonstrating real-time speech recognition integrated with drone communication.

---

## How It Works

1. Microphone captures audio input continuously
2. Speech recognition engine converts speech to text
3. Recognized text is matched against a predefined command set
4. Matched command is sent to the Pluto drone via `plutocontrol`
5. Drone executes the corresponding flight action

---

## Architecture

```
Audio Input Thread                   Drone Control Thread
┌──────────────────────────┐        ┌──────────────────────────┐
│ Microphone Capture       │ shared │ Read recognized command  │
│ Speech-to-Text Engine    │─state─>│ Map to drone action      │
│ Command Matching         │ (lock) │ Send via plutocontrol    │
└──────────────────────────┘        └──────────────────────────┘
```

---

## Suggested Voice Commands

| Voice Command | Drone Action     |
|---------------|------------------|
| "Take off"    | Arm + Takeoff    |
| "Land"        | Land + Disarm    |
| "Forward"     | Pitch Forward    |
| "Backward"    | Pitch Backward   |
| "Left"        | Roll Left        |
| "Right"       | Roll Right       |
| "Turn left"   | Yaw Left         |
| "Turn right"  | Yaw Right        |
| "Stop"        | Neutral / Hold   |

---

## Guidelines to Build This

1. **Set up audio capture** — Use `pyaudio` or `sounddevice` to capture microphone input
2. **Choose a speech recognition approach**:
   - `speech_recognition` library with Google Speech API (easy, requires internet)
   - `vosk` for offline recognition (no internet needed, recommended for real-time)
   - `whisper` (OpenAI) for high accuracy but higher latency
3. **Build a command parser** — Map recognized text to drone commands using keyword matching or fuzzy matching
4. **Implement a two-threaded design** — One thread for continuous listening, another for sending drone commands. The drone control thread must **send commands continuously at ~10Hz**, repeating the last recognized command until a new one arrives. This is how the Pluto drone works — it expects a constant stream of commands to stay in flight
5. **Add confirmation feedback** — Use `pyttsx3` or terminal prints to confirm which command was recognized
6. **Handle noise and errors** — Add a confidence threshold to avoid false triggers
7. **Integrate with `plutocontrol`** — Send the mapped commands to the drone. When no voice command is active, the drone thread should still send neutral throttle values to maintain altitude

---

## Requirements

Suggested Python packages:

```bash
pip install plutocontrol SpeechRecognition pyaudio
# OR for offline recognition:
pip install plutocontrol vosk sounddevice
```

---

## How to Run

1. Connect your laptop to the Pluto drone WiFi
2. Ensure your microphone is working
3. Run your script:

```bash
python main.py
```

4. Speak commands clearly to control the drone
5. Say **"Land"** or press **Ctrl+C** to safely stop

---

## Hardware Used

* Pluto X / Pluto 1.2 Drone
* Laptop with microphone (Python environment)

---

## Key Challenges to Solve

* **Continuous command stream** — The Pluto drone requires commands to be sent continuously; design your drone thread to keep sending the active command in a loop, not just once per voice input
* **Latency** — Speech recognition can be slow; choose a fast engine for real-time control. Keep the drone control thread running independently so flight stays smooth during recognition delays
* **Noise handling** — Drone motors create significant noise; consider noise cancellation, a directional mic, or keeping the mic away from the drone
* **Command ambiguity** — Handle similar-sounding words gracefully
* **Thread safety** — Ensure shared state between listener and drone threads is properly locked
* **Short command windows** — Keep voice commands short (one or two words) for faster recognition and quicker drone response

---

## Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)

---

## Future Scope

* Add multilingual voice support
* Combine with hand gesture control for hybrid input
* Add voice feedback using text-to-speech
* Implement custom wake word (e.g., "Hey Pluto")
* Use NLP for natural sentence commands (e.g., "fly forward for 3 seconds")
