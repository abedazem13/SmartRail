# SmartRail — presentation and submission checklist

**Target:** 18 October 2026. **Prepared:** 13 October 2026. An unchecked item means open, not failed. Assign owners together; the repository currently describes shared team ownership, not a fixed per-member split.

## 1. Clarify with course staff now

- [ ] Confirm that the date/time and 35% weight apply to this team's presentation.
- [ ] Confirm presentation length, questions time, attendance and language.
- [ ] Confirm submission system, exact deadline time, required format (Markdown/PDF/PPTX/video/archive) and naming rules.
- [ ] Confirm whether this milestone requires the complete agreed feature list or permits the hybrid availability prototype.
- [ ] Specifically clarify `FR-007`: must the quantitative Gaussian-versus-uniform passenger-flow/dwell-time comparison be included now?
- [ ] Confirm that two real sensors plus 1,294 clearly labeled simulated seats, logical cars and a laptop passenger display are acceptable.
- [ ] Confirm whether USB is acceptable for the current demonstration or whether an actual wireless ESP32-to-platform link is required.
- [ ] Confirm any additional report, poster, video, source/binary or attribution requirements. The image alone does not establish these.

Suggested message:

> For October 18, we plan to demonstrate SmartRail's 12-car availability display using two real ESP32 sensor seats and 1,294 simulated seats, with user and programmer manuals. The ESP32 link is USB; optional phone viewing uses the laptop's local network. Random station stops animate occupancy but do not quantify dwell-time improvement. Does this satisfy the required scope for this milestone, or must the quantitative passenger-flow comparison and/or wireless train link also be demonstrated? Please confirm the presentation duration, submission format and exact deadline.

Keep the response or a permitted summary with the submission evidence. Do not mark approval based on silence.

## 2. Suggested work plan

| When | Priority outcome | Owner |
|---|---|---|
| 13 Oct | Confirm scope/formats; review this package; allocate narrator, software operator and hardware operator | Team to assign |
| 14–15 Oct | Test current code + actual two-sensor integration; fix reproduced issues; record real evidence | Team to assign |
| 16 Oct | Update manuals/slides from actual results; capture screenshots/photos and backup video | Team to assign |
| 17 Oct | Full timed rehearsal on intended laptop/network; freeze the tested revision; verify exports | Team to assign |
| 18 Oct | Follow setup checklist, present the frozen version and submit all required deliverables | Team |

These are planning suggestions, not additional course deadlines. If time is short, agree a reduced scope with staff rather than silently omitting requirements.

## 3. Documentation and claims

- [ ] Overview states 12 logical cars × 108 seats and only two physical sensor inputs.
- [ ] Slides distinguish implemented behavior, software-tested behavior, physically tested behavior and future work.
- [ ] User manual matches actual button labels, port setup, modes and network operation.
- [ ] Programmer manual matches actual message formats, endpoints, train size, thresholds and simulator behavior.
- [ ] Record actual ESP32 core and other tool versions; older documents disagree or leave TODOs.
- [ ] Do not submit obsolete three-car counts, old green/yellow thresholds, retained-on-tie behavior, or claims that every mode change resets station 1.
- [ ] Explain “full” as no free seats, not standing capacity.
- [ ] Do not present random Next stop animation as a validated dwell-time experiment.
- [ ] Preserve old dated test reports as history; do not rewrite their pass counts for a newer revision.
- [ ] Source links work in the repository; exported documents include usable references.
- [ ] Obtain permission/attribution for any external images, charts or media used in slides. Use original current screenshots where possible.

## 4. Software readiness

- [ ] Record Git commit, branch and whether local changes exist.
- [ ] Install dependencies with the interpreter used to launch the presentation.
- [ ] Run the current unittest suite; save complete output and actual test count.
- [ ] Run the optional browser check or document a manual browser test if not run; never report an unrun automated check as passed.
- [ ] Verify simulation example: 311 free, station 1, top cars L/J/E; A=12, B=3, C=0.
- [ ] Verify both tabs synchronize; passenger page has no seat-edit controls.
- [ ] Verify presets, next stop, auto start/stop and pending-animation behavior.
- [ ] Verify failed server requests hide old counts and successful requests recover.
- [ ] Test screen resolution/projector readability; control maps can be scrolled but passenger information should be understandable at viewing distance.

## 5. Hardware readiness — only operators with the device can complete

- [ ] Confirm actual board and sensor models, wiring and common ground.
- [ ] Power down before wiring; follow course power rules; record capacitor installation and measured noise.
- [ ] Record absolute empty/occupied distances for both sensors; validate range and mounting.
- [ ] Compile and upload the tested firmware, preserving toolchain/build evidence.
- [ ] Test firmware seat 0→A1 and seat 1→B1 independently.
- [ ] Complete ten occupy/vacate cycles per sensor with latency and false-event observations.
- [ ] Check real seats remain locked through clicks, presets, Next stop and auto stops.
- [ ] Check calibration, USB loss, reconnect and reset on the presentation computer.
- [ ] Preserve a dated report and actual video/screenshots; the fact that the previous hardware presentation happened is insufficient.

Use [TEST_RESULTS_TEMPLATE.md](TEST_RESULTS_TEMPLATE.md); leave unperformed checks NOT RUN.

## 6. Live-demo preparation

- [ ] Assign narrator, dashboard operator and hardware operator; all understand the system and can answer questions.
- [ ] Rehearse [DEMO_SCRIPT.md](DEMO_SCRIPT.md) without improvising setup.
- [ ] Stop auto before the sensor segment and use the one-free-seat-per-real-car scene.
- [ ] Close Arduino Serial Monitor/Plotter and all other COM readers.
- [ ] Prepare spare USB data cable, power/charger, adapters and safe spare wires; do not rebuild a tested breadboard moments before presenting.
- [ ] Test optional phone display on a trusted network; keep a laptop-only fallback.
- [ ] Have a backup recording of a real run, clearly dated/labeled; if none exists, do not pretend a software recording proves hardware behavior.
- [ ] Plan what to say if hardware/network fails; disclose simulation fallback explicitly.
- [ ] Disable disruptive notifications and avoid exposing private files or credentials on the projected screen.

## 7. Submission bundle

- [ ] Project overview/documentation.
- [ ] User manual.
- [ ] Programmer manual.
- [ ] Final slide deck if required; [the Markdown outline](SLIDES_AND_SPEAKER_NOTES.md) is not itself a PPTX.
- [ ] Completed test report and linked actual evidence.
- [ ] Current screenshots, wiring photo and permitted video location, following [asset guidance](assets/README.md).
- [ ] Tested source revision, dependency versions and any required firmware build provenance.
- [ ] Check rendered PDFs: diagrams, Hebrew/English text, tables and links.
- [ ] Confirm no secrets, personal data, machine-specific private paths or unintended generated files are included.
- [ ] Commit/push the intended bundle when the team explicitly approves; verify teammates can retrieve it.
- [ ] Submit through the course's specified system and preserve confirmation.

## 8. Final readiness decision

Fill only after rehearsal:

| Item | Result |
|---|---|
| Tested commit and clean/dirty state | TODO |
| Approved presentation scope / evidence | TODO |
| Software verification | NOT RECORDED HERE |
| Current physical integration | NOT RECORDED HERE |
| Required manuals/export formats ready | TODO |
| Remaining blockers and owners | TODO |
| Decision | NOT YET ASSESSED — ready / ready with explicitly approved limitations / not ready |