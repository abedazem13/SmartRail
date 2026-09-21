# Open Questions

| ID | Question | Why it matters | Owner | Priority | Status | Answer/evidence |
|---|---|---|---|---|---|---|
| Q-01 | Team member names and area ownership | README, status file, course requirement | Team | High | Answered | Yazan Rabea, Abed Azem, Samar Khatib. All work jointly on all areas [R, 2026-09-21] |
| Q-02 | Installed ESP32 Arduino core version | Reproducible builds, README field | Team | High | Open | |
| Q-03 | Absolute empty and occupied distances (not just the ~40 cm gap) | Confirms both are inside 15–80 cm | Team | High | Partly answered | Empty ≈ 50–60 cm [R, 2026-09-21]. Occupied still to be measured; estimated 10–20 cm, possibly too close |
| Q-04 | Fit 10 µF capacitors? | Datasheet recommendation, noise | Team | Medium | Decided for now | Not fitted — member's choice [R, 2026-09-21]. Revisit if measured `noise` exceeds ~150 mV |
| Q-05 | Is the current wiring as in 05_WIRING_AND_PINOUT.md? | An earlier photo suggested wrong rows and unpowered rails | Team | High | Partly answered | Sensor red wire on VIN [R, 2026-09-21]. USB power and signal row not confirmed |
| Q-06 | How many seats in the final demo model? | Hardware request, NUM_SEATS | Team | Medium | Open | Two sensors wired now, `NUM_SEATS 2` [R, 2026-09-21]. Final count not decided |
| Q-07 | Car → platform channel: ESP-NOW, WiFi+Firebase, other? | Architecture | Team + mentor | Medium | Open | Not decided yet [R, 2026-09-21] |
| Q-08 | Platform display hardware | Hardware request (course advises no new hardware after POC) | Team | Medium | Open | Not decided yet [R, 2026-09-21] |
| Q-09 | Simulation metric and 2-minute demo format | Course requires agreeing this for algorithmic elements | Team + mentor | High | Open | |
| Q-10 | Is a Flutter app in scope? (`flutter_app/` exists in the template) | Scope, documentation | Team + mentor | Medium | Open | Not decided yet [R, 2026-09-21] |
| Q-11 | What exactly the "35%" in the hardware announcement refers to vs the grading breakdown (50/30/20) | Effort planning | Team | Low | Open | |
| Q-12 | Arduino IDE vs PlatformIO for all members | Course asks for one IDE per team | Team | Low | Answered | All members use Arduino IDE [R, 2026-09-21] |
| Q-13 | Semester start date (week 1) | Convert course deck week numbers into calendar deadlines | Team | Medium | Closed | Summer semester, week plan not applicable; team is up to date [R, 2026-09-21] |
| Q-14 | Who is the direct mentor? | Significant decisions must be sent to the mentor in writing | Team | Medium | Answered | Itai Dabran [R, 2026-09-21] |
| Q-15 | Which seats belong to which carriage in the demo model? | `CARRIAGES` in `PC_software/seat_live.py`, guidance output | Team | Medium | Open | Default: seat 0 → car 1, seat 1 → car 2 [assumption] |
| Q-16 | Python and pyserial versions used | Reproducible PC setup, README | Team | Low | Open | |
