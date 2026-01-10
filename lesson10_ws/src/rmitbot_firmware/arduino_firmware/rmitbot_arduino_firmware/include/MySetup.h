// ==============================================
// Pin definitions for the encoders
// ==============================================
#define ENC1_A 39 // big back, m1
#define ENC1_B 36 // big back, m1

#define ENC2_A 27 // big tape, m2
#define ENC2_B 14 // big tape, m2

#define ENC3_A 34 // smol back, m3
#define ENC3_B 35 // smol back, m3

#define ENC4_A 18 // smol tape, m4
#define ENC4_B 4  // smol tape, m4

// ==============================================
// Pin definitions for the motors
// ==============================================
#define MOT1_A 32 // big back, m1
#define MOT1_B 33 // big back, m1

#define MOT2_A 13 // big tape, m2
#define MOT2_B 12 // big tape, m2

#define MOT3_A 26 // smol back, m3
#define MOT3_B 25 // smol back, m3

#define MOT4_A 19 // smol tape ,m4
#define MOT4_B 23 // smol tape ,m4

// ==============================================
// PWM Channel definitions for the motors
// ==============================================
#define PWM1_A 4 // big back, m1
#define PWM1_B 5 // big back, m1

#define PWM2_A 0 // big tape, m2
#define PWM2_B 1 // big tape, m2

#define PWM3_A 6 // smol back, m3
#define PWM3_B 7 // smol back, m3

#define PWM4_A 2 // smol tape, m4
#define PWM4_B 3 // smol tape, m4

// ==============================================
// IMU Pin definitions
// ==============================================
// #define I2C_SDA 23 // Pin used on ESP32 for I2C SDA
// #define I2C_SCL 22 // Pin used on ESP32 for I2C SCL

// ==============================================
// Variables
// ==============================================
unsigned long Serial_time = 0; // Serial time in us
double w1, w1_ref, MOT1_cmd;   // Speed, reference ,and command for the motor 1
double w2, w2_ref, MOT2_cmd;   // Speed, reference ,and command for the motor 2
double w3, w3_ref, MOT3_cmd;   // Speed, reference ,and command for the motor 3
double w4, w4_ref, MOT4_cmd;   // Speed, reference ,and command for the motor 4
volatile long EncoderTick1;    // Encoder tick count for encoder 1
volatile long EncoderTick2;    // Encoder tick count for encoder 2
volatile long EncoderTick3;    // Encoder tick count for encoder 3
volatile long EncoderTick4;    // Encoder tick count for encoder 4
double quat[4];                // Store the quaternion data
double gyr[3];                 // Store the gyro data
double acc[3];                 // Store the accel data
double quat_calib[4];          // Store the quaternion data
double gyr_calib[3];           // Store the gyro data
double acc_calib[3];           // Store the accel data
