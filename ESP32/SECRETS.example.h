#ifndef _SECRETS_H
#define _SECRETS_H
// Template for ESP32/SECRETS.h
//
// 1. Copy this file to ESP32/SECRETS.h
// 2. Fill in the real values in the copy
// 3. Never commit SECRETS.h. It is listed in .gitignore.
//
// Not used yet: the hardware-feasibility firmware has no network code.
// Needed from the communication stage (WiFi) onward.

const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

#endif  // _SECRETS_H
