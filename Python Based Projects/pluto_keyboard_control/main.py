from plutocontrol import Pluto
import sys
import tty
import termios

# Function to capture single key press (without pressing Enter)
def get_key():
    fd = sys.stdin.fileno()  # Get file descriptor of terminal
    old_settings = termios.tcgetattr(fd)  # Save current terminal settings
    try:
        tty.setraw(fd)  # Set terminal to raw mode (instant key capture)
        key = sys.stdin.read(1)  # Read one character
    finally:
        # Restore original terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

# Initialize and connect to the drone
drone = Pluto()
drone.connect()

# Flag to track whether drone is armed (prevents repeated arming)
armed = False

# Display control instructions
print("Controls: w/a/s/d, space=takeoff, l=land, x=stop, q=quit")

# Main control loop
while True:
    key = get_key()  # Read key input in real-time

    # Takeoff sequence (only if not already armed)
    if key == " " and not armed:
        print("Takeoff")
        drone.arm()        # Arm the drone (enable motors)
        drone.take_off()   # Initiate takeoff
        armed = True

    # Landing sequence
    elif key == "l":
        print("Landing")
        drone.land()       # Land the drone safely
        drone.disarm()     # Disarm motors after landing
        armed = False

    # Forward movement
    elif key == "w":
        print("Forward")
        drone.forward()

    # Backward movement
    elif key == "s":
        print("Backward")
        drone.backward()

    # Left movement
    elif key == "a":
        print("Left")
        drone.left()

    # Right movement
    elif key == "d":
        print("Right")
        drone.right()

    # Stop (reset all movement commands)
    elif key == "x":
        print("Stop")
        drone.reset()

    # Exit program safely
    elif key == "q":
        print("Exit")
        drone.land()       # Ensure drone lands before exit
        drone.disarm()     # Disarm motors
        break