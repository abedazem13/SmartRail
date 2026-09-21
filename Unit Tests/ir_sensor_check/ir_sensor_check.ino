/*
 * Unit test: GP2Y0A21YK0F IR distance sensor bring-up (both sensors)
 * ------------------------------------------------------------
 * Makes no decisions - only prints what each sensor outputs, plus a
 * noise figure. Run this BEFORE the main firmware to validate wiring.
 *
 * Wiring (both sensors):
 *   red    -> VIN   (~5 V when the board is USB powered)
 *   black  -> GND
 *   yellow -> GPIO34 (seat 0), GPIO35 (seat 1)
 *   10 uF capacitor between VIN and GND, right next to each sensor
 *   (recommended by the datasheet; see Documentation/04_HARDWARE.md)
 *
 * Serial monitor: 115200. For each sensor:
 *   raw     : raw ADC count (0-4095)
 *   mV      : average of N samples, factory-calibrated
 *   volt    : same in volts
 *   cm      : datasheet fit d = 29.988 * V^-1.173  (">80" = no reflection)
 *             only valid 10-80 cm
 *   noise   : max - min over the N samples [mV]. <100 good, >150 check capacitor
 * ------------------------------------------------------------
 */

#include <Arduino.h>
#include <math.h>

const uint8_t  N_SENSORS = 2;
const uint8_t  SENSOR_PINS[N_SENSORS] = {34, 35};
const uint8_t  N         = 20;   // samples per line
const uint16_t SAMPLE_MS = 40;   // sensor updates every ~38 ms
const uint32_t PERIOD_MS = 200;

void printSensor(int raw, float avgMv, uint16_t noise) {
  float volts = avgMv / 1000.0f;
  float cm    = (volts < 0.35f) ? -1.0f : 29.988f * powf(volts, -1.173f);

  Serial.print(raw);       Serial.print('\t');
  Serial.print(avgMv, 0);  Serial.print('\t');
  Serial.print(volts, 3);  Serial.print('\t');
  if (cm < 0) Serial.print(F(">80"));
  else        Serial.print(cm, 1);
  Serial.print('\t');
  Serial.print(noise);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  for (uint8_t s = 0; s < N_SENSORS; s++) {
    // Full range up to ~3.1 V. ADC_11db is the Arduino-core name
    // (ADC_ATTEN_DB_12 does not compile on the team's installed core).
    analogSetPinAttenuation(SENSOR_PINS[s], ADC_11db);
  }

  Serial.println();
  Serial.println(F("GP2Y0A21YK0F sensor check - seat 0 = GPIO34, seat 1 = GPIO35"));
  Serial.println(F("S0 raw\tmV\tvolt\tcm\tnoise\t|  S1 raw\tmV\tvolt\tcm\tnoise"));
  Serial.println(F("------------------------------------------------------------------------"));
}

void loop() {
  uint32_t sumMv[N_SENSORS] = {0};
  uint16_t minMv[N_SENSORS], maxMv[N_SENSORS];
  int      lastRaw[N_SENSORS] = {0};
  for (uint8_t s = 0; s < N_SENSORS; s++) { minMv[s] = 65535; maxMv[s] = 0; }

  for (uint8_t i = 0; i < N; i++) {
    for (uint8_t s = 0; s < N_SENSORS; s++) {
      lastRaw[s] = analogRead(SENSOR_PINS[s]);
      uint16_t mv = analogReadMilliVolts(SENSOR_PINS[s]);
      sumMv[s] += mv;
      if (mv < minMv[s]) minMv[s] = mv;
      if (mv > maxMv[s]) maxMv[s] = mv;
    }
    delay(SAMPLE_MS);
  }

  for (uint8_t s = 0; s < N_SENSORS; s++) {
    if (s > 0) Serial.print(F("\t|  "));
    printSensor(lastRaw[s], sumMv[s] / (float)N, maxMv[s] - minMv[s]);
  }
  Serial.println();

  delay(PERIOD_MS);
}
