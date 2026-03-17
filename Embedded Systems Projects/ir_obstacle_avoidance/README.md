# Obstacle Avoidance Drone using `irsense` (IR SENSOR MODULE)

## Project Idea

Build a drone that can **detect nearby obstacles and automatically avoid collisions** using the `irsense`- an Infrared (IR) sensor module.

---

## Objective

Enable **basic autonomous safety behavior** in a drone using a simple, low-cost IR sensor add-on.

---

## How It Works

1. `irsense` continuously monitors the area in front of the drone
2. **Normal state** → sensor outputs `HIGH` (no obstacle)
3. **Obstacle detected** → sensor output drops to `LOW`
4. Drone reacts by **reversing pitch** to move away from the obstacle
5. A fixed-duration timer (~1 second) holds the avoidance maneuver before the drone stabilizes and resumes normal flight

---

## Hardware Used

| Component | Details |
| --------- | ------- |
| Flight Controller | Primus v5 / Primus X2 |
| Sensor | `irsense` — IR Sensor Module |

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
    → Obstacle detected
    → Apply reverse pitch/roll
    → Hold for ~1 second
    → Reset controls
  Else:
    → Resume normal flight
```

---

## Purchase Links

- [Pluto Drone Kit](https://dronaaviation.com/store/)
- [irsense / IR Sensor Add-on](https://dronaaviation.com/store/)

---