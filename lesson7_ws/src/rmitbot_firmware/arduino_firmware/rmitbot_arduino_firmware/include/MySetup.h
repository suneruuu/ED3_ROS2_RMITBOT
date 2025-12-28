
// ==============================================
// Pin definitions for the encoders
// ==============================================
#define ENC1_A 34 // Pin used on ESP32 for the ENC1_A
#define ENC1_B 35 // Pin used on ESP32 for the ENC1_B (big tape), motor 2

#define ENC1_C 18
#define ENC1_D 4 //smol tape, m4

#define ENC1_E 39 
#define ENC1_F 36 //big back, m1

#define ENC1_G 27
#define ENC1_H 14 //smol back, m3

// ==============================================
// Pin definitions for the motors
// // ==============================================
#define MOT1_A 26 // Pin used on ESP32 for the MOT1_A
#define MOT1_B 25 // Pin used on ESP32 for the MOT1_B (big tape), m2

#define MOT1_C 23
#define MOT1_D 19 // smol tape ,m4

#define MOT1_E 32
#define MOT1_F 33 // big back, m1

#define MOT1_G 13
#define MOT1_H 12 // smol back, m3

// ==============================================
// PWM Channel definitions for the motors
// ==============================================
#define PWM1_A 0 // PWM Channel attached to MOT1_A
#define PWM1_B 1 // PWM Channel attached to MOT1_B (big tape)

#define PWM1_C 2
#define PWM1_D 3 // smol tape

#define PWM1_E 4
#define PWM1_F 5 // big back
#define PWM1_G 6
#define PWM1_H 7 // smol back

// ==============================================
// Variables
// ==============================================
unsigned long Serial_time = 0; // Serial time in us
double w1, w1_ref, MOT1_cmd;   // Speed, reference ,and command for the motor 1
volatile long EncoderTick1;    // Encoder tick count for encoder 1


double w2, w2_ref, MOT2_cmd;   // Speed, reference ,and command for the motor 2
volatile long EncoderTick2;  


double w3, w3_ref, MOT3_cmd;   // Speed, reference ,and command for the motor 3
volatile long EncoderTick3;   


double w4, w4_ref, MOT4_cmd;   // Speed, reference ,and command for the motor 4
volatile long EncoderTick4;   

// ==============================================
// IMU Variables
// ==============================================
double quat[4];   // Quaternion data from the IMU
double gyr[3];    // Gyroscope data from the IMU
double acc[3];    // Accelerometer data from the IMU   