# SmartRail poster

One page, **67 cm wide × 97 cm high**, built in the course template (ICST, 97x67 R2).

- **Submit/print:** [SmartRail_Poster.pdf](SmartRail_Poster.pdf). Print at actual size (100%), not scaled to A4.
- **Edit in PowerPoint:** [SmartRail_Poster.pptx](SmartRail_Poster.pptx)
- **Quick preview:** [SmartRail_Poster_preview.png](SmartRail_Poster_preview.png)

## What is on it

- Tagline "Spread out. Board faster." The description (54 pt) covers the problem, what SmartRail is, three features (seat sensing, platform map, phone app) and the simulated result: stops 22% shorter.
- An editable system diagram with steps 1–6, from seat sensor to the platform map and phone app.
- Two native PowerPoint charts with values from `simulation/boarding_sim.py` at its default parameters: boarders per carriage with and without the platform map, and mean dwell against compliance for the stage 3 display and the stage 2 "three best cars" display.
- The platform screen and phone app figures from [simulation/figures](../simulation/figures), and the seat-sensor prototype photo in [input/stage3](input/stage3).
- Captions are 38 pt, above the template's 36 pt minimum; six graphics, the template's maximum.

The 22% is a simulation result, not a station measurement, and the poster says "in simulation".

## Rebuilding

```powershell
python -m pip install -r Poster/requirements.txt
python Poster/build_poster.py
```

This overwrites `SmartRail_Poster.pptx` from [the course template](input/course-poster-template.pptx). Manual PowerPoint edits do not survive a rebuild unless they are also made in `build_poster.py`. Export the PDF from PowerPoint (File → Export → PDF, standard quality) and keep the page size.

If the simulation is re-run with different parameters, update the chart values in `build_poster.py` to match.

**Credits:** Yazan Rabea, Abed Azem, Samar Khatib. Instructors: Itai Dabran, Diana Cohen, Ido Ram.
