# Keyboard Controlled Pluto Drone (Python)

##  Project Idea

Control the Pluto drone in real-time using **keyboard inputs** via Python, without using a traditional remote controller.

---

##  Objective

Enable **software-based manual control** of the drone using a laptop keyboard, demonstrating communication between Python and the Pluto drone.

---

##  How It Works

1. Python script captures keyboard inputs (W, A, S, D, etc.)
2. Commands are mapped to drone movements
3. Commands are sent to Pluto drone using `plutocontrol` package
4. Drone responds in real-time

---

##  Requirements

Install required Python package:

```bash
pip install plutocontrol
```

---

##  Controls

| Key   | Action    |
| ----- | --------- |
| W     | Forward   |
| S     | Backward  |
| A     | Left      |
| D     | Right     |
| Q     | Yaw Left  |
| E     | Yaw Right |
| Space | Takeoff   |
| L     | Land      |

---

##  Hardware Used

* Pluto X / Pluto 1.2 Drone
* Laptop (Python environment)

---

## 🛒 Purchase Links

* [Pluto Drone Kit](https://dronaaviation.com/store/)

---

## 🔮 Future Scope

* GUI-based control panel
* Gamepad / joystick integration
* Web-based control dashboard
* AI-assisted flight control