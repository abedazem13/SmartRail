# SmartRail — slides and speaker notes

**Editable outline, not a rendered slide deck.** Copy the “On slide” content into your preferred slide tool. Use speaker notes for explanations, not as dense slide text. Suggested presentation length: 6–8 minutes plus questions; confirm the actual allowance. Roles below are suggestions for the team to assign, not existing ownership decisions.

## Slide 1 — SmartRail: see availability before boarding

**On slide**
- Seat sensing + passenger-facing platform display.
- Yazan Rabea · Abed Azem · Samar Khatib.
- Hybrid prototype: two real seats inside a larger simulated train.

**Say**
> SmartRail explores how train-seat availability can help passengers decide where to wait on the platform. Today we will show the sensor-to-screen path and a multi-car demo, and clearly distinguish real hardware from simulation.

**Visual:** passenger-screen screenshot from the current version. See [asset plan](assets/README.md).

## Slide 2 — The problem and proposed information

**On slide**
- Passengers may cluster near some doors.
- Seat availability can differ between cars.
- Show car availability and corresponding platform zones.

**Say**
> Instead of discovering seat availability only after entering a car, a passenger could look at the platform display first. We hypothesize that better information may help distribute boarding, but this presentation does not claim a measured dwell-time reduction.

**Avoid:** invented field-study statistics or an improvement percentage.

## Slide 3 — How data reaches the screen

**On slide**
1. IR sensor measures distance to the seat/target.
2. ESP32 calibrates and decides EMPTY/OCCUPIED.
3. USB sends state messages to the laptop.
4. Python aggregates availability; browser displays it.

**Say**
> The occupancy decision is made on the ESP32. The laptop does not guess occupancy from raw voltage. It groups seat states into cars, maintains unknown states if data is lost, and updates both browser views.

**Visual:** architecture diagram from [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md), plus an actual wiring photo when available.

## Slide 4 — What is real, and what is simulated?

**On slide**
- 12 logical cars × 108 seats = 1,296 seats.
- Hybrid: A1 and B1 use the two physical sensors.
- Other 1,294 seats are simulated.
- Operator controls and passenger display are separate.

**Say**
> We do not have a physical train with 1,296 sensors. The two physical inputs prove the integration path once tested, while simulated seats let us exercise a larger train display. Software-only mode is also available for development.

**Visual:** control-screen map showing outlined A1/B1 and the mode label.

## Slide 5 — What passengers see

**On slide**
- Confirmed free seats and occupancy per car.
- Green: 10+ free; amber: 1–9; red: no free seats.
- Gray: incomplete data, not assumed free.
- Up to three cars with the most confirmed free seats.

**Say**
> The recommendation is a simple availability ranking with alphabetical tie-breaking. It is not a reservation and does not guarantee a seat. “Full” refers to the monitored seats, not standing capacity.

**Live cue:** example scenario, station 1. Show A=12, B=3, C=0 and suggestions L/J/E in simulation mode.

## Slide 6 — Live demonstration

**On slide**
- Physical target → seat state → updated count.
- Manual simulated seats → same display.
- Next stop → visible simulated alighting/boarding.
- USB loss → unknown, not falsely free.

**Say / do**
Use [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Stop auto mode before showing the real inputs. Prepare the hybrid “all simulated seats occupied” scene so each physical input visibly changes a car between one free seat and zero.

**Roles to assign:** one narrator, one controls operator, one hardware operator. The narrator should not also search menus or rewire the breadboard.

**Fallback:** show a saved recording of an actually tested hardware run, or explicitly switch to software-only mode. Never silently substitute simulated sensor values.

## Slide 7 — Validation and current limits

**On slide**
- Automated model/API/browser tests: insert actual current run result.
- Physical cycles and response times: insert measured results or “not yet verified”.
- USB disconnect/recovery: insert actual result.
- No quantitative dwell-time claim.

**Say**
> We separate software tests using fake serial inputs from measurements on the actual board. Here is the tested revision and the evidence for what we demonstrated.

**Before presenting:** replace these instructions with facts from the completed [test report](TEST_RESULTS_TEMPLATE.md). Do not copy the old 30-test report as proof of the current 12-car version. If results are absent, state the gap.

## Slide 8 — Deliverables and next steps

**On slide**
- Live prototype and reproducible setup.
- User manual and programmer manual.
- Test evidence, limitations and next work.
- Future: wireless deployment and quantitative passenger-flow evaluation.

**Say**
> The present prototype demonstrates seat-state collection and display integration. The next work is to validate it thoroughly and evaluate the broader passenger-distribution hypothesis under agreed assumptions.

**Close:** show the repository/presentation entry point and the exact tested revision.

---

## Likely questions and honest answers

**Why use simulated seats?**  
We have two physical sensors. Simulated inputs demonstrate multi-car aggregation and display behavior without claiming a physically instrumented full train.

**Why is a capacitor relevant?**  
The sensor draws pulsed current. The recommended bypass capacitor helps stabilize its supply; it does not extend the valid measurement range or fix bad mounting. State what is actually installed, with measurements.

**Is the link wireless?**  
The ESP32-to-laptop link is USB. A phone may view the laptop's passenger page over a trusted LAN; that is a different link.

**Does “Next stop” prove faster boarding?**  
No. It randomly changes simulated occupancy. It does not calculate walking distance, door queues, boarding rate or train dwell time.

**What if everyone follows the same suggestion?**  
Current suggestions rank availability only; they do not observe or control the crowd. Passenger assignment and quantitative balancing require additional modeling and evaluation.

**Can an unknown sensor be counted free?**  
No. Calibration and stale/disconnected serial data produce unknown. The software still cannot detect every electrical fault if firmware continues reporting plausible states.

**What if all seats are occupied?**  
The display reports no free seats and does not suggest a car on the basis of nonexistent availability. It does not decide whether standing passengers may board.

**Is this production ready?**  
No. It is a course prototype with explicit simulated inputs, local memory-only state and unfinished deployment/evaluation work.

**Why not Flutter or a separate monitor?**  
A browser display meets the development need and can run on the laptop or an optional phone. Course acceptance of the final format must be confirmed separately.