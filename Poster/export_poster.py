"""Export using installed Microsoft PowerPoint, without changing shell policies."""

import argparse
import json
from pathlib import Path

import pymupdf
import pythoncom
from win32com.client import DispatchEx

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE / "SmartRail_Poster.pptx")
    parser.add_argument("--pdf", type=Path, default=HERE / "SmartRail_Poster.pdf")
    args = parser.parse_args()
    pythoncom.CoInitialize()
    app = presentation = None
    overflow = []
    try:
        app = DispatchEx("PowerPoint.Application")
        presentation = app.Presentations.Open(str(args.input.resolve()), -1, 0, 0)
        # ppSaveAsPDF = 32; preserve the original slide/page dimensions.
        presentation.SaveAs(str(args.pdf.resolve()), 32)
        for slide in presentation.Slides:
            for shape in slide.Shapes:
                if shape.HasTextFrame == -1 and shape.TextFrame.HasText == -1:
                    frame = shape.TextFrame2
                    available = shape.Height - frame.MarginTop - frame.MarginBottom
                    if frame.TextRange.BoundHeight > available + 2:
                        overflow.append({"name": shape.Name, "height_pt": frame.TextRange.BoundHeight,
                                         "available_pt": available})
    finally:
        if presentation is not None:
            presentation.Close()
        if app is not None and app.Presentations.Count == 0:
            app.Quit()
        pythoncom.CoUninitialize()

    with pymupdf.open(args.pdf) as pdf:
        assert len(pdf) == 1, "Poster must be one page"
        page = pdf[0]
        dimensions = [round(page.rect.width / 72 * 2.54, 3), round(page.rect.height / 72 * 2.54, 3)]
        assert abs(dimensions[0] - 67) < 0.1 and abs(dimensions[1] - 97) < 0.1
        text = page.get_text()
        for value in ("SmartRail", "1,294", "1,296", "Yazan", "Abed", "Samar",
                      "Itai Dabran", "Diana Cohen", "Ido Ram"):
            assert value in text, f"Expected text missing from rendered PDF: {value}"
        assert "github" not in text.lower(), "Repository line must not appear on the revised poster"
        assert text.count("Team:") == 1 and text.count("Mentors:") == 1, "Credits must appear exactly once"
        for placeholder in ("<Project name>", "Team member names", "photos and graphics", "tagline - Short teaser"):
            assert placeholder not in text, f"Template placeholder remains: {placeholder}"
        page.get_pixmap(matrix=pymupdf.Matrix(0.7, 0.7), alpha=False).save(HERE / "SmartRail_Poster_preview.png")
        layout = json.loads((HERE / "generated" / "poster-layout.json").read_text(encoding="utf-8"))
        if "process_bounds_cm" in layout:
            x, y, width, height = layout["process_bounds_cm"]
            cm_to_pt = 72 / 2.54
            clip = pymupdf.Rect(x * cm_to_pt, y * cm_to_pt,
                                (x + width) * cm_to_pt, (y + height) * cm_to_pt)
            page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), clip=clip, alpha=False).save(
                HERE / "SmartRail_Process_Diagram.png")
        report = {"pdf": args.pdf.name, "pages": len(pdf), "page_cm": dimensions,
                  "possible_text_overflow": overflow,
                  "images": len(page.get_images()), "text_characters": len(text),
                  "template_placeholders_found": False,
                  "process_diagram_exported": "process_bounds_cm" in layout}
        (HERE / "generated" / "pdf-validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("PDF and preview exported. Inspect the preview before submitting.")


if __name__ == "__main__":
    main()