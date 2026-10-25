# report_new_app

Stage 3 work, kept in one folder so that nothing in the rest of the repository
is overwritten. Everything here is new; no existing SmartRail file is replaced.

    PC_software/dispatcher.py            the routing rule the phone app serves
    PC_software/platform_view.py         what a platform entrance screen may show
    PC_software/passenger_routes.py      Flask routes for both interfaces
    PC_software/passenger_web/           the two UIs (platform map, phone app)
    PC_software/guidance.py              a rewritten guidance.py (see below)
    PC_software/tests/                   76 tests pinning the design constraints
    PC_software/PASSENGER_INTERFACES.md  how both components work and why
    Documentation/SmartRail_Report_2.docx  the current stage 3 report
    Documentation/SmartRail_Report_1.docx  an earlier, superseded draft
    Documentation/build_report.js          regenerates the report from source
    Documentation/report_assets/           figures and the stage 2 guides it embeds
    simulation/                          the boarding model and its figures

## Running it

The two interfaces run on their own, without touching the existing dashboard:

    cd report_new_app/PC_software
    python passenger_routes.py

    Platform screen: http://127.0.0.1:8766/platform
    Phone app:       http://127.0.0.1:8766/app

## Running the tests

    cd report_new_app/PC_software
    python -m unittest discover -s tests -p "test_*.py"

76 tests should pass. The suite reaches sideways into `../../PC_software` for
the team's `dashboard_model.py` and `dashboard.py`, so it must stay two levels
below the repository root to find them. If those files move, the tests that
need them skip with a message rather than failing.

## About PC_software/guidance.py

This is a rewritten version of the file of the same name in the repository's
own `PC_software/`. It keeps the public names and return shapes, so
`seat_live.py` and `seat_sim.py` would keep working, but the rule underneath
routes each passenger to the least-loaded carriage within walking range instead
of the nearest one with a free seat.

**It is not active.** The repository's `PC_software/guidance.py` is untouched
and is still what the console tools import. The copy here is the proposed
replacement, kept separate so this folder changes nothing. To adopt it, copy it
over the original and run the full suite from `PC_software`, where 126 tests
should pass: the existing ones plus these.

## Regenerating the report

    cd report_new_app/Documentation
    npm install docx
    node build_report.js

It reads figures from `report_assets/img` and embeds the stage 2 guides from
`report_assets/stage2` verbatim, so Appendices D and E cannot drift from what
is in `Presentation/`. The output is written next to the script as
`SmartRail_Report.docx`.

Note that `report_assets/stage2/USER_MANUAL.md` is a copy taken from
`Presentation/USER_MANUAL.md` at the time of writing. If that file changes,
copy it across and rebuild so Appendix E stays in step.

## About the simulation folder

`simulation/israel_journey.py` and the GTFS scripts are kept because they are
real work, but the current report no longer covers them: the Israel Railways
calibration was cut, and the crush-load result that justifies the screen's
20 percent fallback is now measured in the generic model instead.
