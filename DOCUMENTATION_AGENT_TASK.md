# SmartRail — Complete Documentation Task for an AI Agent

## Purpose

This file is a task specification for the AI agent helping the current project members.

The goal is to document **everything a new teammate needs to understand, build, run, test, debug, modify, and present the SmartRail project without relying on undocumented knowledge**.

The documentation may be long. Completeness, accuracy, traceability, and usefulness to another AI agent are more important than brevity.

---

## Instructions for the AI Agent

You are documenting an existing IoT project named **SmartRail**. It includes hardware, ESP32 firmware, a Flutter application, communication between components, and project documentation.

Do not merely create empty templates. Work with the project members, inspect every relevant repository file, and populate the documentation with verified information.

### Required working method

1. Inspect the complete repository, including source code, configuration, tests, diagrams, assets, and Git history when available.
2. Interview both project members about information that cannot be learned from the repository.
3. Ask questions in small, logically grouped batches so the members can answer accurately.
4. Compare their answers with the code and diagrams.
5. If information conflicts, document the conflict and ask which version is current.
6. Clearly distinguish:
   - **Verified fact** — confirmed by code, hardware, output, diagram, or both members.
   - **Reported fact** — stated by a member but not independently verified.
   - **Assumption** — a temporary interpretation that still needs confirmation.
   - **Unknown/TODO** — information that is missing.
7. Never invent details. Use `TODO: confirm ...` when a fact cannot be established.
8. Record exact versions, model numbers, pin numbers, commands, paths, payloads, units, limits, and error messages whenever applicable.
9. Use Mermaid diagrams, tables, and examples where they improve clarity.
10. Use paths relative to the repository root when referring to files.
11. Do not place passwords, Wi-Fi credentials, API keys, private certificates, personal information, or other secrets in Markdown or Git. Document only the required variable names and safe setup procedure.
12. Before finishing, validate all documented setup/build/run/test steps on a clean environment when practical.
13. Commit the resulting documentation and all relevant existing work, then push it to the shared branch agreed upon by the team.

---

## Required Interview Topics

Ask the two current project members about every topic below. Do not skip a topic merely because it is absent from the repository.

### Project and academic context

- What problem does SmartRail solve?
- Who are the intended users?
- What is the expected demonstration or final product?
- What are the course, sponsor, deadline, grading, poster, report, and presentation requirements?
- What is in scope, out of scope, optional, or planned for later?
- What are the success criteria and measurable requirements?
- What responsibilities does each team member currently own?

### Current state

- What currently works end to end?
- What works only partially?
- What is implemented but untested?
- What is planned but not implemented?
- What is broken or blocked?
- What shortcuts, temporary workarounds, technical debt, and known bugs exist?
- Which branch, commit, firmware build, mobile build, and physical prototype represent the latest working state?

### Hardware

- Exact board and component model numbers.
- Quantity, purpose, electrical requirements, voltage levels, interfaces, and relevant datasheets.
- Pin-to-pin wiring, ESP32 GPIO assignments, power connections, grounds, pull-ups, resistors, level shifters, and other supporting parts.
- Breadboard/PCB/mechanical layout and 3D-printed parts.
- Safe assembly, startup, shutdown, and handling instructions.
- Current consumption, power source, battery behavior, and limitations.
- Components tried and rejected, including reasons.
- Hardware failures, unreliable connections, calibration, environmental constraints, and replacement options.
- Photos and diagrams of the current physical prototype.

### ESP32 firmware

- Exact ESP32 board, framework/core/SDK, IDE/toolchain, partition scheme, flash settings, and library versions.
- Source entry point and code/module structure.
- Boot sequence and runtime control flow.
- Purpose of every task, state, interrupt, timer, sensor read, actuator output, and important function.
- GPIO map and why each pin was selected.
- Configuration constants, thresholds, timings, units, and valid ranges.
- Required secrets and how to provide them safely.
- Build, flash, erase, monitor, and recovery procedures.
- Logging format and how to diagnose boot loops, crashes, connection failures, and peripheral failures.
- Memory, CPU, storage, timing, watchdog, concurrency, and real-time constraints.
- Any generated binaries and how to reproduce them from source.

### Flutter application

- Flutter/Dart versions and supported operating systems/devices.
- App purpose, user flows, screens, navigation, state management, services, models, storage, and package versions.
- Permissions and platform-specific setup.
- Configuration and environment variables.
- Build, run, debug, test, release, and installation procedures.
- How the app discovers, connects to, monitors, and controls the hardware.
- Expected UI state when hardware/network services are unavailable.
- Screenshots or recordings of each important flow.

### Communication and data

- Every communication path: Wi-Fi, Bluetooth/BLE, HTTP, WebSocket, MQTT, serial, cloud service, or other protocol.
- Which component is client/server, central/peripheral, publisher/subscriber, or access point/station.
- Addresses, ports, service/characteristic UUIDs, MQTT topics, endpoints, methods, headers, and QoS where applicable.
- Message schemas and real request/response/event examples.
- Field names, data types, units, ranges, required/optional fields, timestamps, identifiers, and versioning.
- Connection lifecycle, discovery, pairing, authentication, retries, timeouts, reconnection, and offline behavior.
- Data storage, retention, synchronization, and deletion.
- Error messages/codes and their meanings.
- Security and privacy decisions, risks, and unresolved concerns.

### Testing and evidence

- Unit, component, integration, system, usability, performance, and field tests performed.
- Exact test setup and steps.
- Expected versus actual results.
- Date, hardware revision, firmware/app versions, and person performing each test.
- Logs, screenshots, measurements, videos, and other evidence.
- Untested requirements and why they remain untested.
- Repeatable acceptance test for the complete demonstration.

### Decisions, research, and sources

- Alternatives considered for hardware, libraries, architecture, protocols, and UI.
- Why the selected approach was chosen.
- Tradeoffs and constraints.
- Links to datasheets, tutorials, repositories, papers, vendor pages, videos, issue discussions, and other sources actually used.
- Which source influenced which implementation decision.
- License/attribution obligations for copied or adapted code, media, models, and libraries.

---

## Documentation Files to Create

Create the following structure. If equivalent documentation already exists, improve and reorganize it instead of creating conflicting duplicate files.

```text
README.md
Documentation/
├── 00_PROJECT_OVERVIEW.md
├── 01_CURRENT_STATUS_AND_HANDOFF.md
├── 02_REQUIREMENTS_AND_SCOPE.md
├── 03_SYSTEM_ARCHITECTURE.md
├── 04_HARDWARE.md
├── 05_WIRING_AND_PINOUT.md
├── 06_ESP32_FIRMWARE.md
├── 07_FLUTTER_APPLICATION.md
├── 08_COMMUNICATION_AND_DATA.md
├── 09_SETUP_BUILD_AND_RUN.md
├── 10_TESTING_AND_RESULTS.md
├── 11_TROUBLESHOOTING.md
├── 12_DESIGN_DECISIONS.md
├── 13_SECURITY_PRIVACY_AND_SAFETY.md
├── 14_REFERENCES_AND_ATTRIBUTIONS.md
├── 15_GLOSSARY.md
├── 16_DEMO_AND_PRESENTATION.md
├── CHANGELOG.md
├── OPEN_QUESTIONS.md
└── assets/
    ├── diagrams/
    ├── photos/
    ├── screenshots/
    ├── logs/
    └── test-results/
```

### `README.md`

Make this the concise entry point. Include:

- Project name and one-paragraph summary.
- A photo or architecture image if available.
- Main features and current maturity.
- Hardware/software technology summary.
- Quick-start links, not duplicated long instructions.
- Repository folder map.
- Links to every documentation file.
- Team roles and project context.
- License or `TODO` if undecided.

### `00_PROJECT_OVERVIEW.md`

Explain the problem, intended users, use cases, complete behavior, major features, expected demonstration, and a high-level end-to-end scenario.

### `01_CURRENT_STATUS_AND_HANDOFF.md`

This is the first file a returning/new teammate should read. Include:

- Date and commit to which the status applies.
- Latest known working hardware/firmware/app combination.
- Completed, partial, untested, planned, broken, and blocked items.
- Known bugs and limitations.
- Active branches and unmerged work.
- Work owned by each person.
- Immediate next actions, ordered by priority.
- Exact steps to reproduce the latest successful end-to-end run.
- Information only known by one member that should not be lost.

### `02_REQUIREMENTS_AND_SCOPE.md`

Include functional requirements, non-functional requirements, constraints, acceptance criteria, in-scope/out-of-scope items, course deliverables, deadlines, and a requirement status matrix.

Give every requirement a stable ID such as `FR-001`, `NFR-001`, or `SAFE-001`, and connect tests to these IDs.

### `03_SYSTEM_ARCHITECTURE.md`

Include:

- Component diagram.
- Deployment/topology diagram.
- Data/control flow diagrams.
- Important runtime sequence diagrams.
- Responsibility of each component.
- Boundaries between hardware, firmware, app, and external services.
- Startup, normal operation, error, and shutdown flows.
- Architecture constraints and assumptions.

Use Mermaid when possible and store editable source for external diagrams.

### `04_HARDWARE.md`

Include a bill of materials table with:

- Item ID.
- Manufacturer and exact part/model.
- Quantity.
- Purpose.
- Key specifications.
- Voltage/current requirements.
- Interface/protocol.
- Supplier/product link.
- Datasheet link.
- Cost if relevant.
- Current status and known issues.

Also describe power design, physical/mechanical construction, component behavior, calibration, limitations, substitutions, rejected parts, and safe handling.

### `05_WIRING_AND_PINOUT.md`

Include:

- A complete pin mapping table from each component pin to ESP32 pin/power/ground.
- Signal direction and protocol.
- Voltage level and required supporting components.
- Notes about boot strapping, input-only pins, conflicts, unsafe pins, and wiring length/noise.
- Step-by-step assembly instructions.
- Connection diagram and clear prototype photos.
- A cross-check against firmware constants such as those in `ESP32/parameters.h`.
- Revision/date of the documented wiring.

No person should need to infer a connection from a photo alone.

### `06_ESP32_FIRMWARE.md`

Include environment versions, dependencies, source layout, configuration, boot/runtime behavior, state machine, tasks and concurrency, sensor/actuator handling, important APIs/functions, error handling, logging, performance/resource constraints, build/flash/monitor commands, and recovery procedures.

Document every configuration parameter in a table containing name, purpose, default, units, valid range, location, and effect.

### `07_FLUTTER_APPLICATION.md`

Include environment versions, dependencies, supported platforms, source layout, architecture/state management, screens and navigation, user workflows, models/services, permissions, local storage, hardware communication, error/offline states, build/run/test/release steps, and screenshots.

### `08_COMMUNICATION_AND_DATA.md`

Treat this as the authoritative interface contract. Include:

- Network/protocol topology.
- Connection and reconnection lifecycle.
- All endpoints, topics, UUIDs, serial formats, or other channels.
- Complete message/data schemas.
- Real sanitized examples.
- Types, units, constraints, required fields, and error behavior.
- Timeouts, retry policies, ordering, duplication, synchronization, and version compatibility.
- Authentication and encryption behavior.

State explicitly whether each interface description is implemented, planned, or obsolete.

### `09_SETUP_BUILD_AND_RUN.md`

Write clean-machine instructions for:

- Installing tools and exact versions.
- Obtaining the repository and correct branch.
- Safely creating local secret/config files from example files.
- Assembling and powering hardware.
- Installing dependencies.
- Building and flashing firmware.
- Running the serial monitor.
- Building and running the Flutter app.
- Establishing communication.
- Verifying successful operation.
- Producing release artifacts.

Commands must be copyable, paths must be clear, expected output must be described, and platform assumptions must be stated.

### `10_TESTING_AND_RESULTS.md`

Include:

- Test strategy and environment.
- Requirement-to-test traceability matrix.
- Hardware component/unit tests.
- Firmware tests.
- Flutter tests.
- Communication/integration tests.
- End-to-end acceptance test.
- Performance, reliability, power, and failure-recovery tests where applicable.
- Results table with date, versions/revisions, expected result, actual result, pass/fail, operator, and evidence link.
- Known coverage gaps.

Do not state that something is tested without preserving reproducible steps and a result.

### `11_TROUBLESHOOTING.md`

For each known problem, include:

- Observable symptom or exact error.
- Likely causes in priority order.
- Diagnostic steps.
- Fix/workaround.
- How to verify the fix.
- Affected hardware/firmware/app versions.

Cover common setup, flashing, boot, wiring, power, connectivity, protocol, sensor, audio/display/keypad, Flutter, and build failures.

### `12_DESIGN_DECISIONS.md`

Create short Architecture/Engineering Decision Records. Each decision should contain:

- Stable ID and title.
- Date and status: proposed, accepted, superseded, or rejected.
- Context/problem.
- Options considered.
- Chosen option and rationale.
- Consequences and tradeoffs.
- Evidence/source links.
- Superseding decision when applicable.

### `13_SECURITY_PRIVACY_AND_SAFETY.md`

Include threat/risks appropriate to the project, trust boundaries, credentials handling, authentication, encryption, network exposure, user/private data, logging concerns, dependency risks, update process, electrical safety, audio/microphone privacy if applicable, physical hazards, mitigations, and unresolved risks.

Never include real secrets.

### `14_REFERENCES_AND_ATTRIBUTIONS.md`

Record every meaningful source with title, link, access date, what it was used for, and affected component/decision. Include library licenses and attribution requirements for source code, audio, images, 3D models, diagrams, and other assets.

### `15_GLOSSARY.md`

Define project-specific names, abbreviations, states, messages, units, hardware terms, and naming conventions. Record alternate/old names to make repository searches easier.

### `16_DEMO_AND_PRESENTATION.md`

Include demonstration prerequisites, setup checklist, script, expected outputs, fallback plan if connectivity/hardware fails, reset procedure between demonstrations, video backup, talking points, timing, and final submission/presentation checklist.

### `CHANGELOG.md`

Use dated entries to record notable hardware, firmware, app, protocol, documentation, and test changes. Identify breaking changes and migration steps.

### `OPEN_QUESTIONS.md`

Track missing or disputed information in a table:

| ID | Question | Why it matters | Owner | Priority | Status | Answer/evidence |
|---|---|---|---|---|---|---|

Do not allow unresolved facts to disappear into vague TODO comments only.

---

## Required Tables and Traceability

At minimum, the final documentation must contain these authoritative tables:

1. Team responsibilities and ownership.
2. Feature/current-status matrix.
3. Requirements and acceptance criteria.
4. Bill of materials.
5. Wiring and GPIO pin map.
6. Firmware configuration parameters.
7. Flutter/environment configuration.
8. Dependency and tool versions.
9. Communication interfaces and schemas.
10. Error codes/states.
11. Tests and results linked to requirements.
12. Known bugs, risks, limitations, and workarounds.
13. Open questions with owners.
14. External sources, licenses, and attributions.

Use consistent IDs across files so facts can be cross-referenced.

---

## Assets and Evidence Rules

- Put images and other evidence under `Documentation/assets/` using descriptive names.
- Prefer names such as `prototype-front-2026-09-21.jpg`, `wiring-rev-a.svg`, or `test-audio-output-2026-09-21.log`.
- Do not use names such as `image1.jpg`, `new diagram.png`, or `final-final.png`.
- Include the source/editable version of diagrams, not only an exported image.
- Caption each image with date, revision, what it shows, and any important caveat.
- Sanitize logs and screenshots before committing them.
- For large videos or binaries, document their shared location instead of adding them to Git unless the repository policy explicitly allows it.

---

## Secret and Configuration Handling

1. Audit tracked files for credentials before pushing.
2. Real secret files must be ignored by Git.
3. Provide safe example files such as `SECRETS.example.h` or `.env.example` containing placeholder values only.
4. Document each required variable, where to obtain it, and where to place it.
5. If a secret was ever committed, removing the file in a later commit is not sufficient. Inform the team, rotate the secret, and clean Git history using an agreed safe procedure.

---

## Final Quality Checklist

Before marking the documentation task complete, verify that:

- [ ] A new teammate can explain the full system after reading the docs.
- [ ] A new teammate can identify the latest working state and next task.
- [ ] Every physical component has an exact model and purpose.
- [ ] Every electrical connection is documented unambiguously.
- [ ] Wiring documentation agrees with firmware pin definitions.
- [ ] Tool, SDK, package, and library versions are recorded.
- [ ] Firmware can be built and flashed from the documented steps.
- [ ] The Flutter app can be built and run from the documented steps.
- [ ] All component-to-component interfaces have explicit contracts and examples.
- [ ] Secrets are absent and safe configuration examples exist.
- [ ] Important success and failure paths are documented.
- [ ] Requirements link to reproducible tests and preserved results.
- [ ] Known bugs, limitations, technical debt, risks, and workarounds are explicit.
- [ ] Design choices and rejected alternatives are recorded.
- [ ] External sources and licenses are attributed.
- [ ] Diagrams match the current implementation.
- [ ] Every unknown has a tracked question and owner.
- [ ] The final end-to-end demonstration has been repeated using only the written instructions.
- [ ] All documentation links work.
- [ ] Documentation changes are committed and pushed.

---

## Expected Completion Report

When finished, give the project members a report containing:

1. Files created or updated.
2. Repository areas inspected.
3. Interviews completed and contributors consulted.
4. Setup/build/run/test steps actually validated.
5. Conflicts discovered and how they were resolved.
6. Remaining unknowns and their owners.
7. Security or secret-handling issues found, without repeating secret values.
8. Latest verified working hardware/firmware/app combination.
9. Branch and commit containing the documentation.
10. Recommended next three project actions.

The work is not complete merely because the files exist. It is complete when the files contain enough verified information for a person or another AI agent with no prior project knowledge to continue the project safely and effectively.
