# PID Line Follower Bot (Primus X2)

## Project Idea

Build a fast PID-based line follower robot using Pluto X2's flight controller (Primus X2) as the brain, with a Cytron IR array sensor for line detection.

---

## Objective

Demonstrate the versatility of the Primus X2 flight controller by using it beyond drones — as a controller for a ground-based PID line follower bot.

---

## How It Works

1. The Cytron IR array sensor reads the line position via its analog output pin
2. The analog value is read through the ADC pin on Primus X2
3. Error is calculated as the difference from the center target value (1925)
4. A PID controller computes the correction needed
5. Motor speeds are adjusted differentially — left and right motors get `BASE_cmd - pid` and `BASE_cmd + pid`
6. Safety cutoff stops motors when error exceeds threshold (prevents damage)

---

## Sensor Output Reference

| Line Position   | Line Not Found | Left      | Center | Right     | Cross Detected |
|-----------------|----------------|-----------|--------|-----------|----------------|
| Analog (3.3V)   | 0 - 0.33V     | 0.33V     | 1.65V  | 2.97V     | 2.97 - 3.3V   |
| Analog (5V)     | 0 - 0.5V      | 0.5V      | 2.5V   | 4.5V      | 4.5 - 5V      |

---

## PID Constants

| Parameter | Value |
|-----------|-------|
| KP        | 0.38  |
| KI        | 0     |
| KD        | 0.16  |

---

## Motor Control

- Motor input range: **0 to 2000**
  - `1000` = Stop
  - `2000` = Full speed forward
  - `0` = Full speed reverse
- Base speed: **1250**
- Max speed: **1900**

---

## Requirements

- **PlutoIDE** for writing and uploading code to Primus X2
- Primus X2 board with ADC pin available for prototyping

---

## Hardware Used

* Primus X2 (Pluto X2 flight controller board)
* Cytron IR Array Sensor (5 digital + 1 analog output)
* 2-Wheel Rover Chassis
* N20 Motors (x2)
* Castor Ball
* LiPo Battery

---

## How to Run

1. Open PlutoIDE
2. Load the `PlutoPilot.cpp` code
3. Connect Primus X2 via USB
4. Upload the code
5. Activate Developer Mode to start the line follower

---

## Purchase Links

* [Pluto Drone Kit / Primus X2](https://dronaaviation.com/store/)

---

## Future Scope

* Tune PID values for faster line following
* Add intersection detection and decision-making
* Add Bluetooth/WiFi telemetry for real-time PID monitoring
* Implement adaptive speed based on track curvature
