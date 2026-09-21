/*
 * SmartRail - seat occupancy firmware
 * ------------------------------------------------------------
 * Detects whether a train seat is EMPTY or OCCUPIED with a Sharp
 * GP2Y0A21YK0F infrared distance sensor mounted above the seat,
 * pointing down at the lap area.
 *
 * Board : ESP32 DevKit V1 (30-pin, CP2102 USB-UART)
 * IDE   : Arduino IDE 2.x  (open this file; the sketch folder is ESP32/)
 *
 * Tunable values : parameters.h
 * Wiring         : Documentation/05_WIRING_AND_PINOUT.md
 * Firmware notes : Documentation/06_ESP32_FIRMWARE.md
 *
 * Serial monitor 115200 baud. Commands:
 *   c  recalibrate (all seats must be empty)
 *   d  toggle raw-voltage debug output
 * ------------------------------------------------------------
 */

#include <Arduino.h>
#include <math.h>
#include "parameters.h"

// ================= State =================

struct Seat {
  uint16_t buf[MEDIAN_WINDOW];  // ring buffer of samples [mV]
  uint8_t  idx;
  bool     filled;

  float    baseline;            // distance to the empty seat [cm]
  float    dist;                // current filtered distance [cm]
  uint16_t noiseMv;             // max - min inside the window [mV]

  bool     occupied;
  bool     pending;             // a state change is waiting to be confirmed
  uint32_t pendingSince;
};

Seat     seats[NUM_SEATS];
uint32_t lastSample = 0;
uint32_t lastPrint  = 0;
bool     debugRaw   = false;

// ================= Sensor layer =================

void setupAdc(uint8_t pin) {
  // Full range up to ~3.1 V. ADC_11db is the Arduino-core name; the IDF name
  // ADC_ATTEN_DB_12 is not declared on the team's installed core (compile error).
  analogSetPinAttenuation(pin, ADC_11db);
}

void pushSample(Seat &s, uint8_t pin) {
  s.buf[s.idx] = analogReadMilliVolts(pin);  // uses the factory eFuse calibration
  s.idx = (s.idx + 1) % MEDIAN_WINDOW;
  if (s.idx == 0) s.filled = true;
}

// Median of the window. Optionally returns the spread (max - min).
uint16_t medianMv(const Seat &s, uint16_t *spread) {
  uint8_t n = s.filled ? MEDIAN_WINDOW : s.idx;
  if (n == 0) {
    if (spread) *spread = 0;
    return 0;
  }

  uint16_t t[MEDIAN_WINDOW];
  for (uint8_t i = 0; i < n; i++) t[i] = s.buf[i];
  for (uint8_t i = 1; i < n; i++) {  // insertion sort, n is tiny
    uint16_t k = t[i];
    int8_t j = i - 1;
    while (j >= 0 && t[j] > k) { t[j + 1] = t[j]; j--; }
    t[j + 1] = k;
  }
  if (spread) *spread = t[n - 1] - t[0];
  return t[n / 2];
}

float mvToCm(uint16_t mv) {
  float v = mv / 1000.0f;
  if (v < V_MIN_VALID) return DIST_MAX_CM;
  float d = DIST_COEFF * powf(v, DIST_EXP);
  if (d > DIST_MAX_CM) d = DIST_MAX_CM;
  if (d < DIST_MIN_CM) d = DIST_MIN_CM;
  return d;
}

// ================= Calibration =================

void calibrate() {
  Serial.println();
  Serial.println(F("--- CALIBRATION: keep all seats EMPTY. starting in 3 s ---"));
  delay(3000);

  for (uint8_t i = 0; i < NUM_SEATS; i++) {
    Seat &s = seats[i];
    s.idx = 0;
    s.filled = false;
    for (uint8_t k = 0; k < MEDIAN_WINDOW * 2; k++) {  // fill the window twice
      pushSample(s, SENSOR_PINS[i]);
      delay(SAMPLE_INTERVAL_MS);
    }

    uint16_t spread;
    uint16_t mv  = medianMv(s, &spread);
    s.baseline   = mvToCm(mv);
    s.dist       = s.baseline;
    s.noiseMv    = spread;
    s.occupied   = false;
    s.pending    = false;
    digitalWrite(LED_PINS[i], LOW);

    Serial.printf("CAL seat=%u baseline=%.1fcm mv=%u noise=%umV\n",
                  i, s.baseline, mv, spread);

    if (spread > NOISE_WARN_MV)
      Serial.println(F("  WARN noise too high: check bypass capacitor and wiring"));
    if (s.baseline < BASELINE_MIN_CM)
      Serial.println(F("  WARN baseline too close: move sensor farther from the seat"));
    if (s.baseline > BASELINE_MAX_CM)
      Serial.println(F("  WARN baseline too far or no reflection: check aim/mounting"));
  }
  Serial.println(F("--- calibration done ---"));
  Serial.println();
}

// ================= Occupancy logic =================

void updateState(uint8_t i) {
  Seat &s = seats[i];
  if (!s.filled) return;

  uint16_t spread;
  s.dist    = mvToCm(medianMv(s, &spread));
  s.noiseMv = spread;

  // Occupied = something is clearly closer than the empty seat.
  // Different thresholds for entering and leaving give hysteresis.
  bool want = s.occupied ? (s.dist < s.baseline - MARGIN_EXIT_CM)
                         : (s.dist < s.baseline - MARGIN_ENTER_CM);

  if (want == s.occupied) {  // no change requested
    s.pending = false;
    return;
  }

  if (!s.pending) {          // first sample asking for a change
    s.pending = true;
    s.pendingSince = millis();
    return;
  }

  if (millis() - s.pendingSince >= STABLE_MS) {  // held long enough
    s.occupied = want;
    s.pending  = false;
    digitalWrite(LED_PINS[i], want ? HIGH : LOW);
    Serial.printf("EVENT seat=%u state=%s dist=%.1fcm\n",
                  i, want ? "OCCUPIED" : "EMPTY", s.dist);
  }
}

// ================= setup / loop =================

void setup() {
  Serial.begin(115200);
  delay(500);

  for (uint8_t i = 0; i < NUM_SEATS; i++) {
    setupAdc(SENSOR_PINS[i]);
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
    seats[i].idx = 0;
    seats[i].filled = false;
  }

  Serial.println();
  Serial.println(F("SmartRail seat occupancy - GP2Y0A21YK0F"));
  Serial.printf("seats=%u window=%u sample=%ums enter=%.0fcm exit=%.0fcm stable=%ums\n",
                NUM_SEATS, MEDIAN_WINDOW, SAMPLE_INTERVAL_MS,
                MARGIN_ENTER_CM, MARGIN_EXIT_CM, STABLE_MS);
  Serial.println(F("commands: c = recalibrate, d = toggle raw debug"));
  calibrate();
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'c') calibrate();
    if (c == 'd') {
      debugRaw = !debugRaw;
      Serial.printf("raw debug %s\n", debugRaw ? "ON" : "OFF");
    }
  }

  // Non-blocking sampling: one sample per seat every SAMPLE_INTERVAL_MS.
  if (millis() - lastSample >= SAMPLE_INTERVAL_MS) {
    lastSample = millis();
    for (uint8_t i = 0; i < NUM_SEATS; i++) {
      pushSample(seats[i], SENSOR_PINS[i]);
      updateState(i);
    }
  }

  if (millis() - lastPrint >= PRINT_INTERVAL_MS) {
    lastPrint = millis();
    for (uint8_t i = 0; i < NUM_SEATS; i++) {
      const Seat &s = seats[i];
      Serial.printf("S%u dist=%5.1fcm base=%5.1fcm noise=%3umV %s%s  ",
                    i, s.dist, s.baseline, s.noiseMv,
                    s.occupied ? "OCCUPIED" : "EMPTY   ",
                    s.pending ? "?" : " ");
      if (debugRaw)
        Serial.printf("(raw=%umV) ", analogReadMilliVolts(SENSOR_PINS[i]));
    }
    Serial.println();
  }
}
