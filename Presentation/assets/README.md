# Presentation assets and evidence

This directory holds presentation screenshots and guidance for the remaining photos, diagrams and logs. No hardware images, recordings or measured hardware results have been fabricated.

## Available for upload to the slide-creation agent

### Passenger dashboard — slide 6

- **File:** [passenger-dashboard-simulation-2026-10-17.png](passenger-dashboard-simulation-2026-10-17.png)
- **Captured:** 17 October 2026, from the actual browser application at source commit `5dcf10f`.
- **Mode:** software simulation; no ESP32, serial worker or physical sensor connected.
- **Scenario:** station 1, 12 cars × 108 seats; 311 free seats. Suggested cars: L (72), J (60), E (48).
- **Image:** high-resolution full-page PNG, 2880 × 3172 pixels (1440 CSS-pixel-wide viewport, 2× pixel scale).
- **Capture:** Microsoft Edge 155.0.4283.45 via Playwright, using an isolated local instance of the existing app. No application source, styles or displayed values were changed for the screenshot.
- **Checks:** all 12 car cards rendered; total 311 and station 1 visible; control panel and error/offline warnings hidden; simulation label present; no uncaught browser exceptions during capture. This is not a full regression run or hardware validation.

Suggested caption:

> SmartRail passenger dashboard in simulation mode: per-car seat availability, occupancy indicators, suggested cars and platform zones.

Upload the PNG itself to the slide-creation agent; a local file path alone does not attach it to another conversation. Keep its aspect ratio. If the full-page image is too tall for slide 6, use clearly labeled detail crops or callouts rather than stretching it or changing the counts. Preserve the fact that the shown values are simulated.

### ESP32 and sensor photograph

No physical prototype photo was found in the repository during this capture. Ask the teammates with the hardware for a clear, current photo of the actual ESP32, both sensors and their wiring. Until then, omit the optional photo or use an explicitly labeled architecture diagram—not a generated image presented as the real prototype.

## Capture list

| ID | Capture | What the caption must say |
|---|---|---|
| IMG-01 | Current 12-car passenger example screen | Date, commit, simulation mode, example scenario, 311 confirmed free |
| IMG-02 | Current control view with A1/B1 visible | Mode, real versus simulated input labels, 12×108 model |
| IMG-03 | Physical board and two-sensor wiring | Actual part models, GPIO34/35, power/ground, capacitor presence, revision/date |
| IMG-04 | Hybrid transition on A1 or B1 | Physical action, before/after state and count; actual hardware only |
| IMG-05 | Unknown after USB loss | Whether real disconnect or mocked software check; do not confuse them |
| IMG-06 | Optional phone displaying passenger page | Trusted network setup and note that ESP32 link is still USB |
| VID-01 | Short backup of a successful real demonstration | Date, tested commit, physical vs simulated inputs and any edits/cuts |
| LOG-01 | Current automated test console output | Interpreter/version, command, commit, actual test count and exit status |
| LOG-02 | Separate physical serial run if collected | Firmware revision, port/baud, actual sensors, measured conditions; not a simultaneous dashboard capture unless actually recorded that way |
| COURSE-01 | Supplied schedule / permitted staff clarification | Original source, date and what was confirmed; screenshot crop alone has missing column headings |

## File and storage conventions

- Use descriptive names with date and mode, not “image1” or “final-final”. Keep small artifacts here or in a clearly linked subfolder.
- Add a caption beside each embedded asset in the slide/manual or a small manifest here with ID, path, date, revision and source.
- Do not link a proposed asset until the file exists.
- Store large videos in an approved shared location rather than Git unless the team explicitly chooses otherwise. Check access from a teammate's account before submitting.
- Keep original/editable diagram sources. The overview's Mermaid diagram is an editable source; export it to SVG/PNG if your slide/PDF tool cannot render Mermaid.
- Use current screenshots. The 9 October nine-seat images do not describe the 12-car model.
- The course image was supplied in chat; it has not been saved into this folder. Add the original only if permitted, without reconstructing missing headings or implying unconfirmed course rules.

## Privacy and accuracy

- Remove credentials, unrelated terminal history, personal browser tabs and private local paths.
- Prefer images of the device and a hand/target rather than identifiable bystanders; obtain consent where needed.
- Clearly label synthetic inputs and screenshots. A rendered UI or mocked test is not physical sensing evidence.
- Do not caption a screenshot “passed” unless the underlying test was executed and recorded.
- Do not add external diagrams/media without attribution or permission to use them.

## Before submission

- [ ] Required current assets captured and captioned.
- [ ] Actual evidence linked in [the test report](../TEST_RESULTS_TEMPLATE.md) and relevant slides/manuals.
- [ ] Video backup opens without relying on venue Wi-Fi.
- [ ] Exported slides/PDFs contain legible images and readable tables.
- [ ] No broken links, secrets or mislabeled hardware claims.