# Drone Laser War System (Laser Tag Sensor)

## Project Idea

Create an interactive **Drone Laser War Game**, where drones can “attack” each other using laser beams.
When a drone gets hit by a laser, it **automatically lands**, simulating a “defeat”.

---

## Objective

Enable a **real-time drone battle system** using laser detection, transforming drones into interactive gaming platforms.

---

## Game Concept

* One drone acts as the **attacker** (equipped with laser emitter)
* Another drone acts as the **target** (equipped with Laser Tag sensor)
* When the target drone is hit by laser → it **lands immediately**

 This creates a **drone vs drone combat scenario**

---

##  How It Works

1. Laser Tag sensor continuously scans for incoming laser light
2. **Normal state** → sensor outputs `HIGH` (no hit)
3. **Laser hit detected** → sensor output becomes `LOW`
4. Drone triggers **auto landing (once)**
5. System resets when dev mode is toggle. (ready for next round)

---

##  Hardware Used

| Component         | Details                 |
| ----------------- | ----------------------- |
| Drone Platform    | Pluto X / Pluto 1.2     |
| Flight Controller | Primus v5 / Primus X2   |
| Sensor            | Laser Tag Sensor Module |
| (Optional)        | Laser Emitter Module    |

---

##  Wiring / Connection

| Pluto RC Port | Laser Tag Pin |
| ------------- | ------------- |
| VCC           | VCC           |
| GND           | GND           |
| Signal        | A0            |

---

##  Core Logic

```id="laserlogic_war"
Loop:
  Read laser sensor output

  If output == LOW AND not already landed:
    → Laser hit detected
    → Trigger landing
    → Set flag = true

  If laser removed:
    → Reset flag (ready for next round)
```

---

##  Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)
* [Laser Tag Sensor Add-on](https://dronaaviation.com/store/)

---

##  Future Scope

* Multi-player drone battle system
* Health system (multiple hits before landing)
* Score tracking & leaderboard
* LED/Buzzer feedback on hit
* Arena-based drone competitions