# Hand-Follow Drone using `irsense` (IR Sensor Module)

## Project Idea

Build a drone that can **detect a hand placed in front of it and move toward it** using the `irsense` — an Infrared (IR) sensor module.

---

## Objective

Enable **basic human-drone interaction** using a simple, low-cost IR sensor add-on.

---

## How It Works

1. `irsense` continuously monitors the area in front of the drone
2. **Normal state** → sensor outputs `HIGH` (no hand detected)
3. **Hand detected** → sensor output drops to `LOW`
4. Drone reacts by **moving forward (pitch)** toward the hand
5. When the hand is removed, the drone stabilizes and stops movement

---

## Hardware Used

| Component         | Details                      |
| ----------------- | ---------------------------- |
| Flight Controller | Primus v5 / Primus X2        |
| Sensor            | `irsense` — IR Sensor Module |

---

## Wiring / Connection

| Pluto RC Port | `irsense` Pin |
| ------------- | ------------- |
| VCC           | VCC           |
| GND           | GND           |
| Signal        | D0            |

---

## Core Logic

```
Loop:
  Read irsense digital output
  If output == LOW:
    → Hand detected
    → Apply forward pitch
  Else:
    → No hand detected
    → Stop / stabilize
```

---

## Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)
* [irsense / IR Sensor Add-on](https://dronaaviation.com/store/)
