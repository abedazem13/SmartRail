# SmartRail poster — PDF and editable source

Prepared **24 October 2026**, after the team reported completing the final presentation. Latest revision uses four equal-sized image panels, removes the repository line, and credits all three user-specified mentors. The two-sentence Problem/SmartRail explanations and six-step process diagram remain. The course template remains the controlling reference.

## Files to use

- **Submit/print:** [SmartRail_Poster.pdf](SmartRail_Poster.pdf)
- **Edit in PowerPoint:** [SmartRail_Poster.pptx](SmartRail_Poster.pptx)
- **Quick preview:** [SmartRail_Poster_preview.png](SmartRail_Poster_preview.png)
- **Process diagram separately:** [SmartRail_Process_Diagram.png](SmartRail_Process_Diagram.png) — also editable inside the PowerPoint

The poster is **one page, 67 cm wide × 97 cm high (portrait)**, matching the actual course template. Print at **actual size / 100%**, not scaled to A4. Use the PDF rather than the preview image for submission or printing. This is a standard PowerPoint PDF, not a separately certified PDF/X or CMYK file; follow any additional print-shop requirements.

## Content and assets

- Original institutional header, master artwork, course footer and logos were preserved from [the course template](input/course-poster-template.pptx), found in the user's Downloads folder and copied here without modifying the original.
- The selected actual photos show the laptop/phone setup and the two physical seat models.
- The selected desktop screenshot is the **operator/control view**; the mobile screenshot is the **passenger view**. Their displayed values illustrate the interface, not measured physical results. Captions identify simulation.
- All four selected images now have identical **27.2 × 14.3 cm** panels in a 2 × 2 grid. The two hardware-photo panels are about **3.8 times the area** of the previous 11.67 × 8.75 cm photos.
- Photographs are center-cropped to focus on the devices. The portrait mobile screenshot uses a contiguous crop of its availability/recommendation section with dark side margins, labeled **simulation detail**, instead of being stretched. Its numbers and recommendation text are unchanged. All input files remain untouched.
- Five visuals: two photos, two screenshots and one six-step process diagram. All supplied originals remain untouched in the input folder.
- **Problem** and **SmartRail** each have two sentences: a core statement followed by context/purpose. Three feature bullets, Advantage, Demonstration and Conclusion remain explicit. **Method / Process** is now a dedicated diagram.
- The process is **Calibrate at startup → Detect using filtered IR → Send a USB state → Merge real and simulated states → Count free seats per car → Display zone guidance**.
- Text states two physical sensor inputs plus 1,294 simulated seats, representing 12 logical cars with 108 seats each. USB sensor transport is distinguished from local Wi-Fi display viewing.
- No measured accuracy, boarding-time reduction, dwell-time improvement or reservation guarantee is claimed.

### Selected photo originals

| Use | Original |
|---|---|
| Laptop and phone | [Selected interface photo](input/WhatsApp%20Image%202026-10-q24%20at%2011.17.08.jpeg) |
| Two physical seat models | [Seat-model photo](input/WhatsApp%20Image%202026-10qq-24%20at%2011.17.07.jpeg) |
| Mobile passenger screenshot | [Selected mobile screenshot](input/WhatsApp%20Image%202026-10-24%20at%2013.38.25.jpeg) |
| Desktop operator screenshot | [Selected desktop screenshot](input/WhatsApp%20Image%202026-10-24%20at%2013.38.32.jpeg) |

All rendered images are embedded, so the editable PowerPoint does not depend on external image links. The source originals remain available above. The process PNG is rendered from the vector diagram in the PDF; it is not a substitute for any selected photo.

## Checks performed

- Opened and exported with installed Microsoft PowerPoint.
- PDF contains one page at approximately 67.001 × 97.003 cm (template rounding).
- Every description-section statement uses **54 pt** text; all new figure captions use **36 pt** or larger.
- Five visual items, below the template's maximum of six; institutional branding is retained separately.
- No vertical text overflow reported by PowerPoint after layout correction.
- PDF text spans are inside the page; expected title, numbers and team names are present.
- Original placeholder instructions are absent from rendered PDF text.
- Header-image bytes and slide-master XML match the original template.
- PDF text fonts are embedded; preview was visually inspected.

See [PDF validation](generated/pdf-validation.json) and [editable layout metadata](generated/poster-layout.json). These are export checks, not hardware test results.

See [TEMPLATE_CHECKLIST.md](TEMPLATE_CHECKLIST.md) for the item-by-item comparison with the original course template. The GitHub/repository line was removed from the poster at the user's request. No replacement contact information was invented.

The initial, simpler poster is preserved for comparison: [original PDF](generated/original-version/SmartRail_Poster.pdf) and [original PowerPoint](generated/original-version/SmartRail_Poster.pptx). Use the files at the top of this page for the revised version.

The revision immediately before this image selection is also preserved: [previous PDF](generated/before-selected-photos/SmartRail_Poster.pdf) and [previous PowerPoint](generated/before-selected-photos/SmartRail_Poster.pptx).

The layout before equal sizing is preserved: [previous image-layout PDF](generated/before-equal-panels/SmartRail_Poster.pdf).

**Credits:** team — **Yazan Rabea, Abed Azem, Samar Khatib**. Mentors — **Itai Dabran, Diana Cohen, Ido Ram**, explicitly requested by the user on 24 October 2026. Confirm the course's submission location and naming requirements before sending.

## Making changes

The simplest workflow is to open the PowerPoint, edit the text/photos, and export PDF using Standard / publishing and printing quality. Preserve the page size. Avoid shrinking the description below 54 pt or captions below 36 pt.

For reproducible generation, [build_poster.py](build_poster.py) creates the PPTX from the copied template and the four selected input images. [export_poster.py](export_poster.py) uses installed Microsoft PowerPoint on Windows to export/validate the PDF and render the standalone process PNG. Dependencies are in [requirements.txt](requirements.txt).

From the SmartRail root, using an existing compatible Python environment:

```powershell
python -m pip install -r Poster/requirements.txt
python Poster/build_poster.py
python Poster/export_poster.py
```

Use the same interpreter for installation and execution. PowerPoint must be installed for export. No changes to Windows script execution policy are needed.

**Warning:** rebuilding overwrites the generated PPTX/PDF; manual PowerPoint edits will not survive a rebuild unless reflected in the builder. Input images/template are not overwritten.

No files were committed or pushed as part of generating this poster.