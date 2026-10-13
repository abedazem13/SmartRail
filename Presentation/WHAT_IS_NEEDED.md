# What is still needed for the presentation?

**Presentation date shown by the course:** 18 October 2026.  
**Checklist prepared:** 13 October 2026. This is the short action list; see [READINESS_CHECKLIST.md](READINESS_CHECKLIST.md) for full details.

## 1. What the course explicitly asks for

The supplied schedule image lists:

1. **Project demonstration.**
2. **Project documentation.**
3. **User manual** — how to install, start and use the system.
4. **Programmer manual** — how the implementation works and how to maintain it.

The exact submission format, deadline time and demonstration scope still need confirmation. Slides, screenshots and a backup video are useful preparation; do not assume the cropped image alone makes each of them a mandatory submission.

## 2. Already prepared — review, do not start from zero

| Material | Current state |
|---|---|
| [Project overview](PROJECT_OVERVIEW.md) | Written; review against the scope approved by the mentor |
| [User manual](USER_MANUAL.md) | Written; verify on the actual presentation computer |
| [Programmer manual](PROGRAMMER_MANUAL.md) | Written against current source; update if implementation changes |
| [Slide outline and speaker notes](SLIDES_AND_SPEAKER_NOTES.md) | Written; not an exported PowerPoint or PDF |
| [Live demo script](DEMO_SCRIPT.md) | Written; needs a timed rehearsal with the actual hardware |
| [Test-results template](TEST_RESULTS_TEMPLATE.md) | Prepared; actual results/evidence still need to be entered |
| [Asset collection guide](assets/README.md) | Prepared; current screenshots, photos and recordings are not supplied by this package |

**Written instructions are not proof that the demo has passed its tests.** The previous hardware presentation happened, but that does not establish validation of the newer dashboard.

## 3. Remaining work — priority order

### Priority 1: confirm what must be demonstrated

- [ ] Ask staff whether the hybrid availability demo is sufficient for October 18.
- [ ] Specifically ask whether the quantitative passenger-distribution/dwell-time simulation (`FR-007`) is required now.
- [ ] Confirm whether USB is acceptable or an actual wireless ESP32-to-platform link is required.
- [ ] Confirm presentation duration, submission format/location, and exact deadline time.

**Do not assume the random “Next stop” animation satisfies the dwell-time simulation requirement.**

### Priority 2: test the current software and real hardware

**Software operator:**
- [ ] Run the current automated tests and save their actual results and tested commit.
- [ ] Verify passenger/control views, simulated seats, presets, Next stop, auto stops and offline behavior on the presentation laptop.

**Teammates who have the hardware:**
- [ ] Confirm safe wiring, sensor range/mounting, capacitor installation and measured noise.
- [ ] Build/upload the current firmware and verify sensor 0 → A1 and sensor 1 → B1.
- [ ] Perform ten occupy/vacate cycles per sensor; record missed/false events and response times.
- [ ] Verify real seats cannot be overwritten by simulated controls.
- [ ] Test calibration, USB disconnect, reconnect and reset with the dashboard.
- [ ] Fill [TEST_RESULTS_TEMPLATE.md](TEST_RESULTS_TEMPLATE.md) with actual observations and evidence; leave unperformed checks NOT RUN.

### Priority 3: finish the presentation material

- [ ] Turn the slide outline into the chosen presentation format, if using slides.
- [ ] Add current passenger/control screenshots, an actual wiring photo and measured test results.
- [ ] Record a short backup of a successful real demonstration, clearly distinguishing physical and simulated inputs.
- [ ] Review both manuals after testing; export PDF or another format only as required by staff.
- [ ] Make every document describe the same tested version. Older documents still contain nine-seat assumptions.

### Priority 4: rehearse and submit

- [ ] Agree who narrates, who operates the dashboard and who handles the sensors.
- [ ] Rehearse the complete demo within the allowed time, including one recovery/failure case.
- [ ] Stop auto stops before demonstrating physical sensor changes; follow [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
- [ ] Test the optional phone/network display beforehand and keep a laptop-only fallback.
- [ ] Bring the tested prototype, laptop/charger, USB data cable, spare cable and required display adapters.
- [ ] Record the final tested commit, commit/push the approved material, and submit through the course's specified system.

## 4. What to say accurately

- The current model has **12 logical cars × 108 seats = 1,296 seats**.
- Hybrid mode has **two real sensor seats and 1,294 simulated seats**.
- The ESP32-to-laptop connection is **USB**. Phone viewing over Wi-Fi is a separate connection.
- The display shows confirmed seat availability; it does not reserve seats or measure standing capacity.
- Random simulated boarding/alighting does **not** demonstrate a measured reduction in train dwell time.

## Bottom line

**The written material is prepared as a draft. The main remaining work is staff confirmation, current-version hardware/software validation, real evidence, final presentation formatting, and rehearsal.**

Do not add a separate monitor, Flutter app, extra sensors or new features merely to fill this checklist. Confirm the required scope first; add missing required features if staff say they belong in this milestone.