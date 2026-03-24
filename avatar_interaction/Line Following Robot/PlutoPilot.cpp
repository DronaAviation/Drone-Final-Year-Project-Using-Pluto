// Do not remove the include below
#include "PlutoPilot.h"
#include "API/API-Utils.h"

/**
 * Configures Pluto's receiver to use PPM or default ESP mode; activate the line
 * matching your setup.
 * AUX channel configurations is only for PPM receivers if no custom configureMode
 * function is called these are the default setup
 * ARM mode : Rx_AUX2, range 1300 to 2100
 * ANGLE mode : Rx_AUX2, range 900 to 2100
 * BARO mode : Rx_AUX3, range 1300 to 2100
 * MAG mode : Rx_AUX1, range 900 to 1300
 * HEADFREE mode : Rx_AUX1, range 1300 to 1700
 * DEV mode : Rx_AUX4, range 1500 to 2100
 */

#define M1_FWD ANTICLOCK_WISE
#define M1_REV CLOCK_WISE
#define M2_FWD CLOCK_WISE
#define M2_REV ANTICLOCK_WISE

#define midVal 2000

#define BASE_cmd  1250 // base speed
#define MAX_cmd   1900 // max speed

// PID constants
#define KP 0.38
#define KI 0
#define KD 0.16

float lastError = 0;
float integral  = 0;

void lfr();

void plutoRxConfig ( void ) {
  // Receiver mode: Uncomment one line for ESP or CAM or PPM setup.
  Receiver_Mode ( Rx_ESP );      // Onboard ESP
  // Receiver_Mode ( Rx_CAM );   // WiFi CAMERA
  // Receiver_Mode ( Rx_PPM );   // PPM based
}

// The setup function is called once at Pluto's hardware startup
void plutoInit() {
  Peripheral_Init(ADC_1);
  Motor_Init(M1);
  Motor_Init(M2);
}

// The function is called once before plutoLoop when you activate Developer Mode
void onLoopStart ( void ) {
  // do your one time stuffs here
}

// The loop function is called in an endless loop
void plutoLoop () {
  lfr();
}

// The function is called once after plutoLoop when you deactivate Developer Mode
void onLoopFinish ( void ) {
  // do your cleanup stuffs here
}

void setMotor(bidirectional_motor_e motor, uint16_t cmd) {
  cmd = constrain(cmd, 0, MAX_cmd);
  if (motor == M1) {
    if (cmd >= 1000) {
      Motor_SetDir(M1, M1_FWD);
      Motor_Set(M1, cmd);
    } else {
      Motor_SetDir(M1, M1_REV);
      Motor_Set(M1, (2000 - cmd));
    }
  } else if (motor == M2) {
    if (cmd >= 1000) {
      Motor_SetDir(M2, M2_FWD);
      Motor_Set(M2, cmd);
    } else {
      Motor_SetDir(M2, M2_REV);
      Motor_Set(M2, (2000 - cmd));
    }
  }
}

void lfr() {
  int16_t error = -(Peripheral_Read(ADC_1) - 1925);
  Monitor_Println("Error Value: ", error);

  if (error >= 1700 || error <= -1700) {
    // Motor stop if error is too high, to avoid damage to the motors
    setMotor(M1, 1000);
    setMotor(M2, 1000);
  } else {
    integral += error;
    integral = constrain(integral, -100, 100);

    float derivative = error - lastError;
    float pid = (KP * error) + (KI * integral) + (KD * derivative);
    lastError = error;

    int leftSpeed  = BASE_cmd - pid;
    int rightSpeed = BASE_cmd + pid;

    setMotor(M1, leftSpeed);
    setMotor(M2, rightSpeed);
  }
}

/*
 * PID Line Follower Bot using Primus X2 flight controller.
 *
 * The robot uses a Cytron IR array sensor (ADC analog output) to detect
 * the line position. The PID controller calculates motor speed adjustments
 * to minimize the error between the sensor reading and the center target
 * value (1925).
 *
 * Motor inputs range from 0 to 2000:
 *   - 1000 = stop
 *   - 2000 = full speed forward
 *   - 0    = full speed reverse
 *
 * Hardware: Primus X2, Cytron IR array sensor, 2-wheel rover chassis,
 *           N20 motors, castor ball.
 */
