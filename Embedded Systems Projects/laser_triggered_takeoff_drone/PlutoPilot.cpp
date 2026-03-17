// Do not remove the include below
#include "PlutoPilot.h"

/**
 * Configures Pluto's receiver to use PPM or default ESP mode; activate the line matching your setup.
 * AUX channel configurations is only for PPM recievers if no custom configureMode function is called this are the default setup
 * ARM mode : Rx_AUX2, range 1300 to 2100
 * ANGLE mode : Rx_AUX2, range 900 to 2100
 * BARO mode : Rx_AUX3, range 1300 to 2100
 * MAG mode : Rx_AUX1, range 900 to 1300
 * HEADFREE mode : Rx_AUX1, range 1300 to 1700
 * DEV mode : Rx_AUX4, range 1500 to 2100
 */
void plutoRxConfig ( void ) {
  // Receiver mode: Uncomment one line for ESP or CAM or PPM setup.
  Receiver_Mode ( Rx_ESP );    // Onboard ESP
  // Receiver_Mode ( Rx_CAM );    // WiFi CAMERA
  // Receiver_Mode ( Rx_PPM );    // PPM based
}

// The setup function is called once at Pluto's hardware startup
void plutoInit ( void ) {
  // Add your hardware initialization code here
  Peripheral_Init ( GPIO_1, INPUT );
}

// The function is called once before plutoLoop when you activate Developer Mode
void onLoopStart ( void ) {
  // do your one time stuffs here
  Set_LED ( STATUS, OFF );
  Set_LED ( BLUE, ON );
}

// The loop function is called in an endless loop
void plutoLoop ( void ) {
  // Add your repeated code here
  if ( Peripheral_Read ( GPIO_1 ) == 0 ) {
    Command_TakeOff ( 170 );
  }
  Set_LED ( RED, ON );
  Set_LED ( GREEN, ON );
}

// The function is called once after plutoLoop when you deactivate Developer Mode
void onLoopFinish ( void ) {
  // do your cleanup stuffs here
  Set_LED ( GREEN, ON );
  Set_LED ( STATUS, ON );
}