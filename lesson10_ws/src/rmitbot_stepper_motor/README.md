# RMITBOT Stepper Motor Controller

ESP32-based stepper motor controller using A4988 driver for NEMA 17 motors.

## Wiring Diagram

```
ESP32          A4988
------         -----
D15 (GPIO15) → STEP
D2  (GPIO2)  → DIR
GND          → GND
              RST ─┬─ SLP (shorted together, connect to VCC)
              EN   (unconnected - pulled low internally = enabled)
              MS1  (unconnected - pulled low = full step)
              MS2  (unconnected - pulled low = full step)
              MS3  (unconnected - pulled low = full step)

A4988 Power:
- VDD: 3.3V-5V logic supply
- VMOT: 8V-35V motor supply
- GND: Common ground with ESP32
- 1A, 1B: Motor coil A
- 2A, 2B: Motor coil B
```

## Serial Commands

Open serial monitor at **115200 baud** and send:

| Command | Action |
|---------|--------|
| `a` | Spin motor **anticlockwise** (CCW) |
| `b` | Spin motor **clockwise** (CW) |
| `c` | **Torque hold** - stop spinning but keep motor energized |
| `o` | **Stop** - no power to motor |

## Building & Uploading

```bash
# Navigate to the project directory
cd rmitbot_stepper_motor

# Build the project
pio run

# Upload to ESP32
pio run --target upload

# Monitor serial output
pio device monitor
```

## Adjusting Speed

Modify `STEP_DELAY_US` in `src/main.cpp`:
- Lower value = faster speed
- Higher value = slower speed
- Default: 1000µs (approximately 500 steps/second)
