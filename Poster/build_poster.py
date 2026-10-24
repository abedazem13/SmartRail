"""Build the editable SmartRail poster in the supplied 67 x 97 cm template.

Original photos and template are never edited. The PDF is rendered separately
by PowerPoint via export_poster.py, so fonts and template branding are retained.
"""

import argparse
import io
import json
import shutil
from pathlib import Path

from PIL import Image, ImageOps
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Cm, Pt

HERE = Path(__file__).resolve().parent
NAVY = "142C3B"
TEAL = "087A78"
MINT = "DDF3ED"
GRAY = "53636E"
WHITE = "FFFFFF"
LINE = "C9DBDE"


def color(value):
    return RGBColor.from_string(value)


class Poster:
    def __init__(self, template):
        self.prs = Presentation(template)
        assert len(self.prs.slides) == 1, "Expected the one-slide course template"
        assert abs(self.prs.slide_width / 360000 - 67) < 0.05
        assert abs(self.prs.slide_height / 360000 - 97) < 0.05
        self.slide = self.prs.slides[0]
        self.editable_text = []
        # Retain the course's header image on the slide and all master artwork.
        # All other slide-level objects are instructions/placeholders.
        for shape in list(self.slide.shapes):
            if shape.shape_id != 23:
                element = shape._element
                element.getparent().remove(element)

    def box(self, x, y, w, h, fill, outline=None, rounded=False, name="panel"):
        kind = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if rounded else MSO_AUTO_SHAPE_TYPE.RECTANGLE
        s = self.slide.shapes.add_shape(kind, Cm(x), Cm(y), Cm(w), Cm(h))
        s.name = name
        if rounded:
            s.adjustments[0] = 0.12
        s.fill.solid()
        s.fill.fore_color.rgb = color(fill)
        if outline:
            s.line.color.rgb = color(outline)
            s.line.width = Pt(1.5)
        else:
            s.line.fill.background()
        return s

    def text(self, text, x, y, w, h, size=54, bold=False, ink=NAVY,
             align=PP_ALIGN.LEFT, name="poster text"):
        s = self.slide.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
        s.name = name
        frame = s.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.auto_size = MSO_AUTO_SIZE.NONE
        frame.margin_left = frame.margin_right = Cm(0)
        frame.margin_top = frame.margin_bottom = Cm(0)
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        for index, line in enumerate(text.split("\n")):
            p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            p.text = line
            p.alignment = align
            p.line_spacing = 1.08
            p.space_before = Pt(0)
            p.space_after = Pt(0)
            for run in p.runs:
                run.font.name = "Arial"
                run.font.size = Pt(size)
                run.font.bold = bold
                run.font.color.rgb = color(ink)
        self.editable_text.append({"name": name, "text": text, "font_pt": size,
                                   "x_cm": x, "y_cm": y, "w_cm": w, "h_cm": h})
        return s

    def photo(self, path, x, y, w, h, *, crop=None, pad=False, name="photo"):
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        if crop:
            image = image.crop(crop)
        if pad:
            # Preserve the whole selected detail inside an equal-size panel.
            # Side margins are background only; no UI values are changed.
            canvas_w = round(max(image.width, image.height * w / h))
            canvas_h = round(max(image.height, image.width * h / w))
            canvas = Image.new("RGB", (canvas_w, canvas_h), "#" + NAVY)
            canvas.paste(image, ((canvas_w - image.width) // 2, (canvas_h - image.height) // 2))
            image = canvas
        # PowerPoint center-crops the embedded image to the frame without
        # stretching it. The original input file remains untouched.
        blob = io.BytesIO()
        image.save(blob, format="PNG")
        blob.seek(0)
        aspect = image.width / image.height
        frame_aspect = w / h
        shape = self.slide.shapes.add_picture(blob, Cm(x), Cm(y), width=Cm(w), height=Cm(h))
        if aspect > frame_aspect:
            trim = (1 - frame_aspect / aspect) / 2
            shape.crop_left = shape.crop_right = trim
        else:
            trim = (1 - aspect / frame_aspect) / 2
            shape.crop_top = shape.crop_bottom = trim
        shape.name = name
        shape.line.color.rgb = color(LINE)
        shape.line.width = Pt(1)
        return shape

    def arrow(self, x, y, w, h, direction="right"):
        kinds = {"right": MSO_AUTO_SHAPE_TYPE.RIGHT_ARROW,
                 "left": MSO_AUTO_SHAPE_TYPE.LEFT_ARROW,
                 "up": MSO_AUTO_SHAPE_TYPE.UP_ARROW,
                 "down": MSO_AUTO_SHAPE_TYPE.DOWN_ARROW}
        s = self.slide.shapes.add_shape(kinds[direction], Cm(x), Cm(y), Cm(w), Cm(h))
        s.name = f"diagram {direction} arrow"
        s.fill.solid()
        s.fill.fore_color.rgb = color(TEAL)
        s.line.fill.background()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=HERE / "input" / "course-poster-template.pptx")
    args = parser.parse_args()
    if not args.template.exists():
        parser.error(f"Template missing: {args.template}")
    canonical = HERE / "input" / "course-poster-template.pptx"
    if args.template.resolve() != canonical.resolve() and not canonical.exists():
        shutil.copy2(args.template, canonical)

    photos = {
        "laptop_phone": HERE / "input" / "WhatsApp Image 2026-10-q24 at 11.17.08.jpeg",
        "seats": HERE / "input" / "WhatsApp Image 2026-10qq-24 at 11.17.07.jpeg",
    }
    screenshots = {
        "passenger": HERE / "input" / "WhatsApp Image 2026-10-24 at 13.38.25.jpeg",
        "controls": HERE / "input" / "WhatsApp Image 2026-10-24 at 13.38.32.jpeg",
    }
    for path in [*photos.values(), *screenshots.values()]:
        if not path.exists():
            parser.error(f"Image missing: {path}")

    p = Poster(args.template)
    p.prs.core_properties.title = "SmartRail — Know where to board"
    p.prs.core_properties.subject = "IoT seat-availability prototype — selected photos and process diagram"
    p.prs.core_properties.author = "Yazan Rabea; Abed Azem; Samar Khatib"
    p.prs.core_properties.keywords = "SmartRail, ESP32, IoT, seat availability, hybrid prototype"

    p.box(5.0, 14.0, 5.6, 5.6, TEAL, rounded=True, name="SmartRail project mark")
    p.text("SR", 5.2, 14.2, 5.2, 5.2, size=102, bold=True, ink=WHITE,
           align=PP_ALIGN.CENTER, name="project logo initials")
    p.text("SmartRail", 12.0, 12.8, 49.5, 6.0, size=136, bold=True, name="project title")
    p.text("Know where to board.", 12.2, 18.9, 49.5, 2.8, size=64, ink=TEAL, name="tagline")
    p.box(4.45, 21.96, 58.2, 63.74, WHITE, name="clean content panel")

    statements = [
        ("Problem: ", "Passengers lack seat information before boarding.\nThey may crowd near one door or search inside the train.", "problem", "B63532"),
        ("SmartRail: ", "Our IoT prototype monitors train-seat availability.\nIt guides passengers toward cars with more free seats.", "project description", NAVY),
        ("Seat sensing: ", "ESP32 and IR sensors detect occupied seats.", "feature 1", TEAL),
        ("Hybrid train: ", "12 x 108 seats (1,296); two physical inputs.", "feature 2", TEAL),
        ("Web guidance: ", "Car counts, seat maps and zone suggestions.", "feature 3", TEAL),
        ("Advantage: ", "Check before boarding, not after entering a car.", "advantages", "265D7E"),
        ("Demonstration: ", "2 physical seats + 1,294 simulated seats.", "demonstration", "265D7E"),
        ("Conclusion: ", "One display combines real and simulated seats.", "conclusion", "265D7E"),
    ]
    y = 22.0
    for label, content, name, label_color in statements:
        lines = content.split("\n")
        height = 4.8 if len(lines) == 2 else 2.34
        is_feature = name.startswith("feature")
        x, width = (6.3, 55.3) if is_feature else (5.4, 56.2)
        if is_feature:
            marker = p.slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, Cm(5.5), Cm(y + 0.9), Cm(0.45), Cm(0.45))
            marker.name = name + " bullet"
            marker.fill.solid()
            marker.fill.fore_color.rgb = color(TEAL)
            marker.line.fill.background()
        shape = p.text(label + content, x, y, width, height, size=54, name=name)
        for index, line in enumerate(lines):
            paragraph = shape.text_frame.paragraphs[index]
            paragraph.clear()
            paragraph.line_spacing = 1.0
            parts = ((label, True, label_color), (line, False, NAVY)) if index == 0 else ((line, False, NAVY),)
            for value, bold, ink in parts:
                run = paragraph.add_run()
                run.text = value
                run.font.name = "Arial"
                run.font.size = Pt(54)
                run.font.bold = bold
                run.font.color.rgb = color(ink)
        y += height + 0.08

    # Explicit process, not just a list of hardware blocks. Every step is editable.
    process_bounds = [5.15, 46.3, 56.7, 5.95]
    p.text("METHOD / PROCESS — FROM SENSING TO GUIDANCE", 5.4, 46.4, 56.2, 1.9,
           size=40, bold=True, ink="265D7E", name="method process caption")
    steps = ["1. Calibrate\nAt startup", "2. Detect\nFiltered IR", "3. Send\nUSB state",
             "4. Merge\nReal + sim.", "5. Count\nFree / car", "6. Guide\nShow zones"]
    for index, text in enumerate(steps):
        x = 5.4 + index * 9.64
        p.box(x, 48.45, 8.0, 3.55, MINT, outline=LINE, rounded=True, name=f"process step {index + 1}")
        p.text(text, x + 0.2, 48.55, 7.6, 3.35, size=36, bold=True,
               align=PP_ALIGN.CENTER, name=f"process label {index + 1}")
        if index < len(steps) - 1:
            p.arrow(x + 8.2, 49.7, 1.25, 0.95)

    # Four equally sized panels give the physical prototype equal prominence.
    # The portrait UI uses a labeled detail crop, padded instead of stretched.
    panel_w, panel_h = 27.2, 14.3
    panels = [
        (photos["laptop_phone"], 5.4, 52.5, "selected actual photo laptop_phone",
         "Laptop + mobile display", "laptop_phone photo caption", None, False),
        (photos["seats"], 34.4, 52.5, "selected actual photo seats",
         "Two sensor seat models", "seats photo caption", None, False),
        (screenshots["controls"], 5.4, 69.1, "selected desktop operator screenshot",
         "Desktop controls (simulation)", "controls screenshot caption", None, False),
        (screenshots["passenger"], 34.4, 69.1, "selected mobile passenger screenshot",
         "Passenger guidance (simulation detail)", "passenger screenshot caption",
         (0, 930, 1116, 1690), True),
    ]
    for path, x, panel_y, name, caption, caption_name, crop, pad in panels:
        p.photo(path, x, panel_y, panel_w, panel_h, crop=crop, pad=pad, name=name)
        p.text(caption, x, panel_y + panel_h + 0.15, panel_w, 1.8,
               size=36, bold=True, ink=GRAY, align=PP_ALIGN.CENTER, name=caption_name)

    # Add credits once, outside the four-image loop.
    p.text("Team: Yazan Rabea  •  Abed Azem  •  Samar Khatib", 5.2, 86.2, 56.5, 2.2,
           size=48, bold=True, align=PP_ALIGN.CENTER, name="team names")
    p.text("Mentors: Itai Dabran  •  Diana Cohen  •  Ido Ram", 5.2, 88.7, 56.5, 1.9,
           size=42, bold=True, ink="265D7E", align=PP_ALIGN.CENTER, name="mentor name")
    p.slide.notes_slide.notes_text_frame.text = (
        "Revised 24 October 2026: Problem and SmartRail each have two sentences. "
        "The four user-selected source images are arranged in equal 27.2 x 14.3 cm panels: "
        "laptop/phone photo, two-seat-model photo, desktop control screenshot, mobile passenger screenshot. "
        "Photos are center-cropped to focus on the prototype. The mobile screenshot uses an explicitly "
        "labeled detail with background padding; no values are changed and input originals are untouched. "
        "Screenshots are labeled simulation, not claimed as sensor measurements. Six process steps show "
        "startup calibration, filtered detection, USB transmission, merging real/simulated states, "
        "per-car counting and platform guidance. Original institutional template retained. "
        "Mentors Itai Dabran, Diana Cohen and Ido Ram credited as requested; repository URL omitted. "
        "No measured accuracy/dwell-time benefit, private email or external collaborator invented."
    )
    out = HERE / "SmartRail_Poster.pptx"
    text_names = [item["name"] for item in p.editable_text]
    assert len(text_names) == len(set(text_names)), "Duplicated poster text boxes"
    p.prs.save(out)
    metadata = {
        "template": str(canonical.relative_to(HERE)),
        "page_cm": [p.prs.slide_width / 360000, p.prs.slide_height / 360000],
        "photos": {k: str(v.relative_to(HERE)) for k, v in photos.items()},
        "screenshots": {k: str(v.relative_to(HERE)) for k, v in screenshots.items()},
        "text_boxes": p.editable_text,
        "figure_count": 5,
        "revision": "equal image panels, no repository line, three mentors",
        "image_panel_size_cm": [panel_w, panel_h],
        "image_panels": [{"name": name, "source": str(path.relative_to(HERE)),
                  "x_cm": x, "y_cm": panel_y, "width_cm": panel_w, "height_cm": panel_h,
                  "detail_crop_px": crop, "background_padding": pad}
                 for path, x, panel_y, name, caption, caption_name, crop, pad in panels],
        "dashboard_size_cm": {"controls": [panel_w, panel_h], "passenger": [panel_w, panel_h]},
        "process_bounds_cm": process_bounds,
        "process_steps": steps,
        "mentors": ["Itai Dabran", "Diana Cohen", "Ido Ram"],
        "repository_line_included": False,
        "original_files_untouched": True,
    }
    (HERE / "generated").mkdir(exist_ok=True)
    (HERE / "generated" / "poster-layout.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created: {out}")
    print(f"Page: {metadata['page_cm'][0]:.3f} x {metadata['page_cm'][1]:.3f} cm")
    print(f"Editable text boxes: {len(p.editable_text)}; visual items: 5; process steps: 6")


if __name__ == "__main__":
    main()