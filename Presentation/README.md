# SmartRail — presentation package

**Target presentation:** 18 October 2026, according to the course schedule image supplied by Abed.  
**Prepared:** 13 October 2026. **Source baseline reviewed:** `0883d93`.  
**Team:** Yazan Rabea, Abed Azem, Samar Khatib. **Mentor:** Itai Dabran (reported in project documentation).

This folder collects the material for explaining, demonstrating, operating and maintaining SmartRail. It describes the current **12-car × 108-seat** implementation, not the earlier nine-seat demo. Existing source and technical documents remain in their original locations; they are linked, not copied or moved.

**Readiness:** populated preparation package, not a claim of completed submission or hardware acceptance. Manuals were checked against source; no new runtime or physical tests were performed while creating this package. Teammates must supply the evidence and approvals tracked below.

## What the course image requests

The visible row says: **“הדגמת הפרויקט, הגשת תעוד, מדריך למשתמש ו־Programmer manual”** — project demonstration, submission of documentation, a user manual, and a programmer manual.

- Date shown: **18/10/2026**.
- **35%** appears to be the milestone weight; verify with the complete rubric.
- The column containing **10** has no visible heading in the supplied crop; do not assume its meaning.
- The crop does not specify presentation length, page counts, file formats, submission system/time, or whether a limited prototype fulfills the milestone. Confirm these with staff.

## Start here

| File | Use it for |
|---|---|
| [WHAT_IS_NEEDED.md](WHAT_IS_NEEDED.md) | Short summary of what is prepared and what still needs to be done before presentation |
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Project explanation, architecture, current scope and limitations |
| [SLIDES_AND_SPEAKER_NOTES.md](SLIDES_AND_SPEAKER_NOTES.md) | Ready-to-adapt slide text, speaking notes and likely questions; Markdown outline, not a PowerPoint export |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Rehearsal and live demonstration, including a high-visibility two-sensor sequence and fallback |
| [USER_MANUAL.md](USER_MANUAL.md) | Installation and operation without needing to understand the code |
| [PROGRAMMER_MANUAL.md](PROGRAMMER_MANUAL.md) | Implementation, configuration, interfaces, tests and extension guidance |
| [READINESS_CHECKLIST.md](READINESS_CHECKLIST.md) | Work to finish, suggested schedule, staff questions and submission checklist |
| [TEST_RESULTS_TEMPLATE.md](TEST_RESULTS_TEMPLATE.md) | Actual final-version software/hardware results; deliberately NOT pre-filled with passes |
| [assets/README.md](assets/README.md) | Which screenshots, photos, logs and backup video to collect, with captions and provenance |

## Suggested reading order

- **Presenters:** overview → slides → demo script → readiness checklist.
- **Operator:** user manual → demo script → test template.
- **Developer / teammate's AI agent:** programmer manual → source → test template.
- **Reviewer:** overview → user manual → programmer manual → completed test report and assets.

## Current demo facts

| Topic | Current implementation |
|---|---|
| Train | 12 logical cars A–L, 108 seats each, 1,296 total |
| Simulation mode | All 1,296 seats software-controlled; no serial device opened |
| Hybrid mode | A1 = sensor 0 / GPIO34, B1 = sensor 1 / GPIO35; remaining 1,294 simulated |
| Physical decision | ESP32; Python receives EMPTY/OCCUPIED, it does not reclassify raw distance |
| Passenger display | Per-car counts/occupancy, up to three car suggestions, platform zones, simulated station number |
| Controls | Seat map, presets, Next stop, auto stops, USB connection and diagnostics |
| Car colors | Green: 10+ confirmed free; amber: 1–9; red: 0 with no unknowns; gray: any unknown |
| Default suggestion | L, J, E in the software example; no seat reservation |
| Demonstration limit | Random simulated boarding/alighting is NOT a dwell-time comparison or proof of optimization |

## Open before calling this submission-ready

1. Staff approval of the intended demo scope, especially the separate `FR-007` quantitative simulation requirement.
2. Final hardware integration tests, calibration/noise measurements and actual latency evidence from teammates.
3. Fresh automated results on the version to be presented; old results are historical, not current certification.
4. Screenshots, wiring photos, backup video and final Git commit reference.
5. Confirmed submission format, deadline time and team presentation roles.

The earlier hardware presentation reportedly happened; its result was not supplied. It is not evidence that the newer full-train dashboard has been tested with the board.

## Documentation consistency

Older [status notes](../Documentation/01_CURRENT_STATUS_AND_HANDOFF.md), [dashboard guide](../Documentation/17_HYBRID_DASHBOARD.md) and [hardware handoff](../Documentation/HARDWARE_DASHBOARD_AGENT_HANDOFF.md) contain nine-seat assumptions, old thresholds or old network restrictions. They remain useful as history, but **do not submit their outdated counts/procedures unchanged**. Use this package for the presentation baseline, and consult current source when anything conflicts.

The [9 October software report](../Documentation/assets/test-results/hybrid-dashboard-software-2026-10-09.md) describes that older revision. Do not rewrite its results to make them appear to test the current model.

## Submission bundle

If staff accept repository Markdown, this folder can be the documentation entry point. If PDFs or slides are required, export the manuals/overview and prepare a slide deck from the slide outline. Check tables, Mermaid diagrams, page breaks and links after export. No PDF, PPTX, photos or video are included yet. Keep the editable Markdown as the source.

Use [the asset guide](assets/README.md) for evidence. Record the actual tested commit after the final changes; this package does not commit or push automatically.