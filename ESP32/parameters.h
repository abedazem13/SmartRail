#ifndef PARAMETERS_H
#define PARAMETERS_H
// SmartRail - user-tunable parameters.
// Change values here, not in ESP32.ino.
// Every parameter is documented in Documentation/06_ESP32_FIRMWARE.md

#include <stdint.h>

// ---------------- Seats and pins ----------------
#define NUM_SEATS 1  // set to 2 after the second sensor is wired

// Sensor analog outputs. ADC1 pins only (GPIO32-39): ADC2 stops working
// when WiFi is enabled. GPIO34/35 are input-only, which is fine for analog.
static const uint8_t SENSOR_PINS[] = {34, 35};

// Status LEDs, one per seat. GPIO2 is the on-board LED of the DevKit V1.
static const uint8_t LED_PINS[] = {2, 4};

static_assert(sizeof(SENSOR_PINS) / sizeof(SENSOR_PINS[0]) >= NUM_SEATS,
              "SENSOR_PINS must have an entry for every seat");
static_assert(sizeof(LED_PINS) / sizeof(LED_PINS[0]) >= NUM_SEATS,
              "LED_PINS must have an entry for every seat");

// ---------------- Sampling ----------------
#define SAMPLE_INTERVAL_MS 40   // matches the sensor update period (~38 ms)
#define MEDIAN_WINDOW      11   // samples in the median window (odd). 11 x 40 ms = 440 ms
#define PRINT_INTERVAL_MS  500  // status line period on the serial monitor

// ---------------- Occupancy decision ----------------
// Measured gap between empty and occupied seat was ~40 cm (reported, Sept 2026).
// Thresholds are derived from that gap.
#define MARGIN_ENTER_CM 20.0f  // OCCUPIED when distance < baseline - 20 cm (half the gap)
#define MARGIN_EXIT_CM  12.0f  // EMPTY again when distance > baseline - 12 cm (hysteresis)
#define STABLE_MS       1000   // a new state must hold this long before it is accepted

// ---------------- Sensor model: Sharp GP2Y0A21YK0F ----------------
// d[cm] = DIST_COEFF * V^DIST_EXP   (fit from the course datasheet slide)
#define DIST_COEFF   29.988f
#define DIST_EXP    -1.173f
#define V_MIN_VALID  0.35f   // below this: no reflection / beyond ~80 cm
#define DIST_MAX_CM  90.0f
#define DIST_MIN_CM  10.0f   // output curve is non-monotonic below ~8 cm

// ---------------- Diagnostics ----------------
#define NOISE_WARN_MV    150    // calibration warns when the sample spread exceeds this
#define BASELINE_MIN_CM  20.0f  // warn if the empty seat reads closer than this
#define BASELINE_MAX_CM  75.0f  // warn if the empty seat reads farther than this

#endif  // PARAMETERS_H
