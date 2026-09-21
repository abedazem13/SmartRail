/*
 * Unit test: GP2Y0A21YK0F IR distance sensor bring-up
 * ------------------------------------------------------------
 * Makes no decisions - only prints what the sensor outputs, plus a
 * noise figure. Run this BEFORE the main firmware to validate wiring.
 *
 * Wiring:
 *   red    -> VIN   (~5 V when the board is USB powered)
 *   black  -> GND
 *   yellow -> GPIO34
 *   10 uF capacitor between VIN and GND, right next to the sensor
 *
 * Serial monitor: 115200. Columns:
 *   raw     : raw ADC count (0-4095)
 *   mV      : average of N samples, factory-calibrated
 *   volt    : same in volts
 *   cm      : datasheet fit d = 29.988 * V^-1.173  (">80" = no reflection)
 *   noise   : max - min over the N samples [mV]. <100 good, >150 check capacitor
 * ------------------------------------------------------------
 */

#include <Arduino.h>
#include <math.h>

const uint8_t  SENSOR_PIN = 34;
const uint8_t  N          = 20;   // samples per line
const uint16_t SAMPLE_MS  = 40;   // sensor updates every ~38 ms
const uint32_t PERIOD_MS  = 200;

void setup() {
  Serial.begin(115200);
  delay(500);
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  analogSetPinAttenuation(SENSOR_PIN, ADC_ATTEN_DB_12);
#else
  analogSetPinAttenuation(SENSOR_PIN, ADC_11db);
#endif

  Serial.println();
  Serial.println(F("GP2Y0A21YK0F sensor check"));
  Serial.println(F("raw\tmV\tvolt\tcm\tnoise(mV)"));
  Serial.println(F("--------------------------------------------"));
}

void loop() {
  uint32_t sumMv = 0;
  uint16_t minMv = 65535, maxMv = 0;
  int      lastRaw = 0;

  for (uint8_t i = 0; i < N; i++) {
    lastRaw = analogRead(SENSOR_PIN);
    uint16_t mv = analogReadMilliVolts(SENSOR_PIN);
    sumMv += mv;
    if (mv < minMv) minMv = mv;
    if (mv > maxMv) maxMv = mv;
    delay(SAMPLE_MS);
  }

  float avgMv = sumMv / (float)N;
  float volts = avgMv / 1000.0f;
  float cm    = (volts < 0.35f) ? -1.0f : 29.988f * powf(volts, -1.173f);

  Serial.print(lastRaw);   Serial.print('\t');
  Serial.print(avgMv, 0);  Serial.print('\t');
  Serial.print(volts, 3);  Serial.print('\t');
  if (cm < 0) Serial.print(F(">80"));
  else        Serial.print(cm, 1);
  Serial.print('\t');
  Serial.println(maxMv - minMv);

  delay(PERIOD_MS);
}
