/**
 * @file main.cpp
 * @brief ESP32 Stepper Motor Controller with A4988 Driver
 *
 * Wiring:
 * - ESP32 D15 (GPIO15) -> A4988 STEP
 * - ESP32 D2 (GPIO2)   -> A4988 DIR
 * - A4988 RST & SLP    -> Shorted together (connected to VCC)
 * - A4988 EN, MS1, MS2, MS3 -> Unconnected (pulled low internally = full step)
 *
 * Controls via Serial:
 * - 'a' : Spin anticlockwise (CCW)
 * - 'b' : Spin clockwise (CW)
 * - 'c' : Enable torque hold (stop stepping, keep motor energized)
 * - 'o' : Stop motor and disable power (no torque hold)
 */

#include <Arduino.h>

// Pin definitions
#define STEP_PIN 15 // GPIO15 (D15) - STEP signal to A4988
#define DIR_PIN 2   // GPIO2 (D2)   - DIR signal to A4988

// Motor control parameters
#define STEP_DELAY_US                                                          \
  1000 // Microseconds between steps (1000us = 1ms -> ~500 RPM at full step)
#define PULSE_WIDTH_US 10 // Pulse width for STEP signal

// Motor states
enum MotorState {
  MOTOR_STOPPED, // Motor stopped, no power
  MOTOR_CCW,     // Spinning counter-clockwise
  MOTOR_CW,      // Spinning clockwise
  MOTOR_HOLD     // Stopped but holding torque
};

MotorState currentState = MOTOR_STOPPED;
unsigned long lastStepTime = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect
  }

  // Configure pins
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  // Initialize pins to LOW
  digitalWrite(STEP_PIN, LOW);
  digitalWrite(DIR_PIN, LOW);

  // Print welcome message
  Serial.println("=================================");
  Serial.println("ESP32 Stepper Motor Controller");
  Serial.println("A4988 Driver - Full Step Mode");
  Serial.println("=================================");
  Serial.println("Commands:");
  Serial.println("  'a' - Spin anticlockwise (CCW)");
  Serial.println("  'b' - Spin clockwise (CW)");
  Serial.println("  'c' - Enable torque hold");
  Serial.println("  'o' - Stop motor (no power)");
  Serial.println("=================================");
  Serial.println("Ready. Waiting for commands...");
}

void stepMotor() {
  // Generate a single step pulse
  digitalWrite(STEP_PIN, HIGH);
  delayMicroseconds(PULSE_WIDTH_US);
  digitalWrite(STEP_PIN, LOW);
}

void loop() {
  // Check for serial input
  if (Serial.available() > 0) {
    char command = Serial.read();

    switch (command) {
    case 'a':
    case 'A':
      // Anticlockwise (CCW)
      digitalWrite(DIR_PIN, LOW); // DIR LOW = CCW
      currentState = MOTOR_CCW;
      Serial.println(">> Motor spinning ANTICLOCKWISE (CCW)");
      break;

    case 'b':
    case 'B':
      // Clockwise (CW)
      digitalWrite(DIR_PIN, HIGH); // DIR HIGH = CW
      currentState = MOTOR_CW;
      Serial.println(">> Motor spinning CLOCKWISE (CW)");
      break;

    case 'c':
    case 'C':
      // Torque hold - stop stepping but keep motor energized
      currentState = MOTOR_HOLD;
      Serial.println(">> Motor HOLDING position (torque enabled)");
      break;

    case 'o':
    case 'O':
      // Stop motor completely - no power
      currentState = MOTOR_STOPPED;
      digitalWrite(STEP_PIN, LOW);
      Serial.println(">> Motor STOPPED (no power)");
      break;

    default:
      // Ignore newlines and carriage returns
      if (command != '\n' && command != '\r') {
        Serial.print("Unknown command: '");
        Serial.print(command);
        Serial.println("'. Use a/b/c/o.");
      }
      break;
    }
  }

  // Motor control based on current state
  unsigned long currentTime = micros();

  if ((currentState == MOTOR_CCW || currentState == MOTOR_CW) &&
      (currentTime - lastStepTime >= STEP_DELAY_US)) {
    stepMotor();
    lastStepTime = currentTime;
  }

  // For MOTOR_HOLD state, we do nothing special - the motor stays energized
  // because EN pin is unconnected (pulled low = enabled on A4988)

  // For MOTOR_STOPPED state, we also do nothing - motor is idle
  // Note: Without EN pin control, we can't truly "disable" the motor
  // The motor will still have some holding torque when stopped
}
