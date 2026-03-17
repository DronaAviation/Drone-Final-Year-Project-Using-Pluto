# Laser Triggered Takeoff Drone (Laser Tag Sensor)

## Project Idea

Build a drone that can **detect laser light and automatically initiate takeoff** using a Laser Tag sensor module.

---

## Objective

Enable **event-based drone activation** using optical sensing, allowing the drone to respond to external laser triggers.

---

## How It Works

1. Laser Tag sensor continuously monitors incoming light
2. **Normal state** → sensor outputs `HIGH` (no laser detected)
3. **Laser detected** → sensor output drops to `LOW`
4. Drone responds by **initiating takeoff (once)**
5. After takeoff, the drone continues under **user control**

---

## Hardware Used

| Component         | Details                 |
| ----------------- | ----------------------- |
| Drone Platform    | Pluto X / Pluto 1.2     |
| Flight Controller | Primus v5 / Primus X2   |
| Sensor            | Laser Tag Sensor Module |

---

## Wiring / Connection

| Pluto RC Port | Laser Tag Pin |
| ------------- | ------------- |
| VCC           | VCC           |
| GND           | GND           |
| Signal        | A0            |

---

## Core Logic

```id="laserlogic_final"
Loop:
  Read laser sensor output

  If output == LOW AND not already taken off:
    → Laser detected
    → Trigger takeoff
    → Set flag = true

  If laser removed:
    → Reset flag (ready for next trigger)

  After takeoff:
    → Allow user control
```

---

## Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)
* [Laser Tag Sensor Add-on](https://dronaaviation.com/store/)

---

## Future Scope

* Laser-based security zones
* Multi-drone laser interaction (tag system)
* Add buzzer/LED feedback on detection
* Restricted area detection using laser boundaries
