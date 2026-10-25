const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageBreak,
  LevelFormat, ExternalHyperlink,
} = require("docx");

const IMG = process.env.SMARTRAIL_IMG || "./report_assets/img/";
const STAGE2 = process.env.SMARTRAIL_STAGE2 || "./report_assets/stage2/";
const INK = "0F172A", MUTE = "475569", LINE = "CBD5E1", TINT = "F1F5F9";
const BODY = 21;            // half-points -> 10.5pt
const CONTENT_W = 9360;     // DXA, A4 with 1" margins

// ---------------------------------------------------------------- helpers --
const p = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 110, line: 264 },
  alignment: o.align,
  indent: o.indent,
  children: [new TextRun({ text, size: o.size ?? BODY, bold: o.bold,
    italics: o.italics, color: o.color ?? INK, font: "Calibri" })],
});

// paragraph from [{t, b, i}] runs
const rich = (runs, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 110, line: 264 },
  alignment: o.align,
  children: runs.map(r => new TextRun({
    text: r.t, bold: r.b, italics: r.i, size: o.size ?? BODY,
    color: r.c ?? o.color ?? INK, font: r.f ?? "Calibri" })),
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, size: 28, bold: true, color: INK, font: "Calibri" })],
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 },
  children: [new TextRun({ text, size: 23, bold: true, color: INK, font: "Calibri" })],
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 80 },
  children: [new TextRun({ text, size: 21, bold: true, color: MUTE, font: "Calibri" })],
});

const bullet = (text, o = {}) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 60, line: 264 },
  children: [new TextRun({ text, size: o.size ?? BODY, color: INK, font: "Calibri" })],
});

// `ref` lets a list restart its numbering instead of continuing the last one.
const numbered = (text, ref = "numbers") => new Paragraph({
  numbering: { reference: ref, level: 0 },
  spacing: { after: 70, line: 280 },
  children: [new TextRun({ text, size: BODY, color: INK, font: "Calibri" })],
});

const code = (text) => new Paragraph({
  spacing: { after: 60, line: 250 }, shading: { type: ShadingType.CLEAR, fill: TINT },
  indent: { left: 180, right: 180 },
  children: [new TextRun({ text, size: 18, font: "Consolas", color: INK })],
});

function figure(file, caption, widthIn = 5.6) {
  const sizeOf = require("child_process").execSync(
    `python3 -c "from PIL import Image;im=Image.open('${IMG}${file}');print(im.size[0],im.size[1])"`
  ).toString().trim().split(" ").map(Number);
  const w = widthIn * 96, h = Math.round(w * sizeOf[1] / sizeOf[0]);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 100, after: 50 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(IMG + file),
        transformation: { width: Math.round(w), height: h } })],
    }),
    rich([{ t: caption, i: true, c: MUTE }],
      { align: AlignmentType.CENTER, size: 17, after: 160 }),
  ];
}

function table(headers, rows, widths) {
  const cell = (text, opts = {}) => new TableCell({
    width: { size: opts.w, type: WidthType.DXA },
    shading: opts.head ? { type: ShadingType.CLEAR, fill: TINT } : undefined,
    margins: { top: 50, bottom: 50, left: 100, right: 100 },
    children: [new Paragraph({
      spacing: { after: 0, line: 250 },
      alignment: opts.right ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: [new TextRun({ text, size: 18, bold: opts.head || opts.bold,
        color: INK, font: "Calibri" })],
    })],
  });
  const numericCol = headers.map((_, i) =>
    rows.length > 0 && rows.every(r => /^[−+-]?[\d.,]+\s*(s|%|m|min)?$|^[-—]$/.test(String(r[i]).trim())));
  return new Table({
    columnWidths: widths,
    borders: ["top", "bottom", "left", "right", "insideHorizontal", "insideVertical"]
      .reduce((a, k) => (a[k] = { style: BorderStyle.SINGLE, size: 2, color: LINE }, a), {}),
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((t, i) =>
        cell(t, { w: widths[i], head: true, right: numericCol[i] })) }),
      ...rows.map(r => new TableRow({ children: r.map((t, i) =>
        cell(String(t), { w: widths[i], right: numericCol[i],
          bold: String(r[0]).startsWith("Whole journey") })) })),
    ],
  });
}

// Three side-by-side slots for the hardware photographs still to be taken.
function photoSlots(labels) {
  const w = Math.floor(CONTENT_W / labels.length);
  return new Table({
    columnWidths: labels.map(() => w),
    borders: ["top", "bottom", "left", "right", "insideHorizontal", "insideVertical"]
      .reduce((a, k) => (a[k] = { style: BorderStyle.DASHED, size: 6, color: "94A3B8" }, a), {}),
    rows: [new TableRow({ children: labels.map(label => new TableCell({
      width: { size: w, type: WidthType.DXA },
      margins: { top: 260, bottom: 260, left: 100, right: 100 },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
          children: [new TextRun({ text: "[ INSERT PHOTO HERE ]", size: 18, bold: true,
            color: "64748B", font: "Calibri" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 },
          children: [new TextRun({ text: label, size: 16, italics: true,
            color: MUTE, font: "Calibri" })] }),
      ],
    })) })],
  });
}

const spacer = (after = 60) => p("", { after });

// ------------------------------------------------- markdown -> paragraphs --
// Used only for the stage-2 guides, which are embedded verbatim from the
// repository so that this document does not drift from what was submitted.
function markdown(file, { demote = 1 } = {}) {
  const lines = fs.readFileSync(STAGE2 + file, "utf8").split(/\r?\n/);
  const out = [];
  let inCode = false, codeBuf = [], tableBuf = [];

  const clean = (s) => s
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\*\*([^*]*)\*\*/g, "$1")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1$2")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1 ($2)")
    .trim();

  const flushTable = () => {
    if (!tableBuf.length) return;
    const rows = tableBuf
      .filter(r => !/^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(r))
      .map(r => r.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map(c => clean(c)));
    tableBuf = [];
    if (rows.length < 2) return;
    const cols = Math.max(...rows.map(r => r.length));
    const norm = rows.map(r => { const c = r.slice(0, cols); while (c.length < cols) c.push(""); return c; });
    const w = Math.floor(CONTENT_W / cols);
    out.push(table(norm[0], norm.slice(1), norm[0].map(() => w)));
    out.push(spacer(80));
  };

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, "");
    if (/^\s*```/.test(line)) {
      if (inCode) { codeBuf.forEach(l => out.push(code(l || " "))); codeBuf = []; }
      inCode = !inCode; continue;
    }
    if (inCode) { codeBuf.push(raw); continue; }
    if (/^\s*\|/.test(line)) { tableBuf.push(line); continue; }
    flushTable();
    if (!line.trim()) continue;

    const head = line.match(/^(#{1,6})\s+(.*)$/);
    if (head) {
      const level = head[1].length + demote;
      const text = clean(head[2]);
      out.push(level <= 2 ? h2(text) : h3(text));
      continue;
    }
    if (/^\s*[-*+]\s+/.test(line)) { out.push(bullet(clean(line.replace(/^\s*[-*+]\s+/, "")), { size: 19 })); continue; }
    const num = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (num) { out.push(bullet(clean(num[1]), { size: 19 })); continue; }
    if (/^\s*>\s?/.test(line)) { out.push(p(clean(line.replace(/^\s*>\s?/, "")), { italics: true, color: MUTE, size: 19 })); continue; }
    if (/^\s*---+\s*$/.test(line)) continue;
    out.push(p(clean(line), { size: 19 }));
  }
  flushTable();
  if (codeBuf.length) codeBuf.forEach(l => out.push(code(l || " ")));
  return out;
}

// ------------------------------------------------------------------ build --
const children = [];

// ------------------------------------------------------------------ title --
children.push(
  rich([{ t: "SmartRail" }], { align: AlignmentType.CENTER, size: 56, after: 60 }),
  rich([{ t: "Seat occupancy sensing and platform guidance for shorter boarding", c: MUTE }],
    { align: AlignmentType.CENTER, size: 24, after: 200 }),
  rich([{ t: "Research document — stage 3", b: true }],
    { align: AlignmentType.CENTER, size: 22, after: 120 }),
  rich([{ t: "Yazan Rabea · Abed Azem · Samar Khatib" }],
    { align: AlignmentType.CENTER, size: 21, after: 60 }),
  rich([{ t: "Mentor: Itai Dabran", c: MUTE }], { align: AlignmentType.CENTER, size: 20, after: 60 }),
  rich([{ t: "236333 Project in Internet of Things · Interdisciplinary Center for Smart Technologies (ICST)", c: MUTE }],
    { align: AlignmentType.CENTER, size: 19, after: 40 }),
  rich([{ t: "Taub Faculty of Computer Science, Technion · October 2026", c: MUTE }],
    { align: AlignmentType.CENTER, size: 19, after: 240 }),
);

// -------------------------------------------------------- general description
children.push(h1("General description"));
children.push(p("SmartRail senses which seats on a train are free and puts that information in front of passengers waiting on the platform, so that they spread along the platform instead of crowding at a few doors. A train cannot leave until its slowest door has finished boarding, so the time it spends standing at a station is set by the busiest door rather than the average one. Spreading the crowd lowers that maximum, and dwell overruns are what accumulate into delay across a journey."));
children.push(p("The prototype has four parts. An infrared distance sensor above each seat reports whether the seat is occupied [1]. An ESP32 microcontroller turns those readings into a stable empty or occupied decision [2]. A laptop groups the seat states into carriages. Two passenger-facing interfaces then present them: a platform entrance screen that draws the train as a positional map, showing each carriage's own free-seat count in the place that carriage will stop, and a phone application that acts as a dispatcher, giving each passenger who asks a different carriage so that the waiting crowd divides itself. Two seats are physically sensed; the remaining 1,294 of a twelve-carriage train are simulated, which lets a whole train be demonstrated without instrumenting it."));
children.push(rich([
  { t: "Headline result. ", b: true },
  { t: "On a twelve-carriage train taking 240 boarding passengers a stop, the positional map cuts mean dwell from 143 to 111 seconds, a saving of 22 percent, and the screen and the application together reach 32 percent. The simulation also showed that a display naming the best carriages makes boarding worse than no display at all, and both interfaces were built around that finding." },
]));

// ---------------------------------------------------------------- introduction
children.push(h1("Introduction"));
children.push(p("Passengers do not spread evenly along a platform. They gather near the entrances, the stairs and the exits they will want at their destination. A few carriages receive most of the boarders while others leave with empty seats, and because the train waits for its slowest door, those crowded doors set the dwell time for the whole train. The information that would fix this already exists on the train, namely which seats are free; it is simply not visible to the person standing on the platform, who must decide where to wait before the train arrives."));
children.push(p("Operators have reached the same conclusion. Deutsche Bahn publishes real-time occupancy per carriage in its passenger app, on the vehicle and on platform displays, using door counters and light sensors, and states the purpose as helping passengers find a seat quickly and helping trains depart on time [8]. Arriva Rail London trialled a system in 2017 that derives how many passengers are in each carriage from train loading data and shows it to station staff, who then direct waiting passengers towards the less crowded carriages [9]. Both confirm that the concept works in service; what neither publishes is a measurement of how much dwell time the guidance actually saves, which is the gap this project addresses."));
children.push(p("SmartRail closes the loop at seat level rather than at door or vehicle level. Seat-level sensing on the train feeds two passenger-facing interfaces, and a simulation estimates what they are worth in seconds of dwell time. The interfaces are deliberately shaped differently because they are read by different numbers of people at once: the platform screen is read by everybody waiting at the same moment, so it carries only positional facts and names no carriage, while the phone application is read by one passenger and may give one instruction precisely because it remembers what it told the previous passenger. Section 5 shows why that asymmetry is the whole design."));
children.push(spacer(80));
children.push(photoSlots([
  "Figure 1a. Sharp IR sensor mounted above a seat, aimed at the lap.",
  "Figure 1b. ESP32 DevKit V1 and both sensors on the breadboard.",
  "Figure 1c. NeoPixel strip standing in for the platform sign.",
]));
children.push(spacer(140));

// ------------------------------------------------------------ work in the field
children.push(h1("Work in the field"));
children.push(p("Counting passengers automatically is not a new idea. A 1979 technical report for the US transit industry evaluated three commercial passenger counters fitted to service buses: one used treadle mats in the door steps and two used infrared beams across the doorway, and the treadle mats performed slightly better under almost all test conditions [12]. The beam-break counter at the door survived that comparison and is still the industry baseline four decades later; the bus fleet studied by Madsen and colleagues in 2022 used exactly that, on twenty-two vehicles [11]."));
children.push(p("The limitation of door counting is structural rather than technological. A door counter measures a flow, not a state, so its estimate of how many people are aboard is an accumulated sum, and any per-event bias accumulates with it. Madsen and colleagues measured a mean drift of about −0.12 passengers per stop against manual ground truth, enough for the running estimate to go negative by the end of a trip, and noted that bicycles, prams and suitcases are counted as people [11]. A door counter also cannot say where the free seats are inside the carriage."));
children.push(p("Four approaches are in use or under study, and they differ in what they actually measure:"));
children.push(bullet("Optical counting at the door. Time-of-flight cameras with active infrared illumination produce a 3D image that a neural network interprets; one manufacturer claims better than 98 percent accuracy independent of ambient light [10]. These are the successors to the 1979 beam counters and inherit the same accumulation problem."));
children.push(bullet("Load weighing. The vehicle weighs itself and infers how many people are aboard. Arriva Rail London's 2017 trial on Class 378 units derived a per-carriage count this way and gave it to station staff, who redirected waiting passengers [9]. It measures a state rather than a flow, so it does not drift, but it cannot tell a heavy passenger from two light ones and says nothing about which seats are free."));
children.push(bullet("Wireless device counting. A receiver counts Wi-Fi probe requests from passengers' phones. It needs a device-per-person conversion factor, derived by Madsen and colleagues from 86 boarding passengers, and thresholds recalibrated for each placement and route [11]: cheap, non-intrusive and correspondingly noisy."));
children.push(bullet("Seat-level sensing, which is what this project does. A sensor per seat measures occupancy directly as a state, so it does not drift and needs no conversion factor, and it is the only approach that answers the question a boarding passenger actually asks: is there a seat in that carriage. The cost is one sensor per seat and the wiring to match, which is why it is rare in service."));
children.push(h2("The sensor"));
children.push(p("Each seat is sensed with a Sharp GP2Y0A21YK0F infrared distance sensor [1]. It emits an infrared pulse and measures the angle at which the reflection returns, so it measures distance by triangulation rather than by reflected intensity. That matters here: the reading barely changes between a light and a dark surface above roughly 20 cm, so clothing colour has little effect, which is the weakness that disqualifies a simple reflective sensor for this job."));
children.push(p("Three properties of the device shaped the design. Its output is not linear, so the firmware converts voltage to distance with the datasheet fit d = 29.988 · V^−1.173 centimetres [1]. It is non-monotonic below about 8 cm, where an object pressed close returns the same voltage as one far away, so the mounting must keep every real reading above roughly 15 cm. Its emitter fires in bursts, which makes the supply sag through breadboard wiring, and the datasheet asks for a bypass capacitor next to the sensor for that reason [1]. The usable range is 10 to 80 cm while a seated person measures about 85 to 90 cm from cushion to head, so the sensor is mounted above the seat and aimed forward at the lap rather than down at the head, putting both the empty and the occupied reading inside the usable range."));

// -------------------------------------------------------- project description
children.push(h1("Project description"));
children.push(h2("Components and assembly"));
children.push(table(
  ["Part", "Qty", "Role"],
  [["ESP32 DevKit V1, 30-pin, CP2102 [2]", "1", "Reads both sensors and decides seat state"],
   ["Sharp GP2Y0A21YK0F IR sensor [1]", "2", "Seat occupancy, 10–80 cm range"],
   ["NeoPixel LED strip", "1", "Platform sign stand-in, one segment per carriage"],
   ["Breadboard, jumper wires, USB cable", "—", "Prototype wiring and power"]],
  [4400, 900, 4060]));
children.push(spacer(100));
children.push(p("Each sensor takes its supply from VIN, which carries about 5 V while the board is powered over USB, and its signal goes to GPIO34 and GPIO35. Those two pins are on ADC1, which continues to work when Wi-Fi is enabled [2]. The sensor's output peaks at about 3.1 V, inside the 3.3 V limit of an ESP32 input, so no divider is needed, but its 5 V supply must never touch a GPIO pin."));
children.push(h2("Algorithms"));
children.push(p("The firmware decides occupancy on the board rather than sending raw readings to the laptop. The threshold is relative to each seat's own measured baseline, which tolerates differences between sensors and mountings better than one fixed distance for every seat, and the later wireless stage needs the decision made on the train. Three mechanisms act together:"));
children.push(numbered("Baseline calibration. At power-on the firmware measures the empty seat for about 0.9 seconds and stores that distance as the seat's baseline.", "proj"));
children.push(numbered("Median filtering. It samples every 40 ms, matching the sensor's own update period, and takes the median of the last eleven samples. A running median rejects isolated spikes without smearing a genuine step change, which is the property a mean does not have [3].", "proj"));
children.push(numbered("Hysteresis. A seat becomes occupied when the filtered distance drops more than 20 cm below its baseline, and returns to empty only when it rises back above baseline minus 12 cm. Two separate thresholds stop the state flickering when a seated passenger shifts; this is the two-threshold switching principle described by Schmitt in 1938 [4]. Any change must then hold for a full second before it is accepted, so somebody walking past a seat never registers.", "proj"));
children.push(p("Detection therefore lags a real movement by about 1.5 seconds, which is well inside the two-second requirement."));
children.push(h2("Communication"));
children.push(p("The board prints a status line twice a second and an event line on every change. These lines are a contract rather than debug output: the laptop parses them, so changing a print format breaks the display. Train and platform are presently joined by the USB cable at 115200 baud. The wireless link a real deployment needs, whether ESP-NOW or Wi-Fi with a cloud database, has not been selected or built, and neither has the platform display hardware; these are the two decisions that gate deployment."));
children.push(h2("The two passenger interfaces"));
children.push(p("A Python program on a laptop reads the serial stream, groups seats into twelve carriages of 108 seats and serves both interfaces over a local HTTP server. The platform screen is a positional map and nothing else: it draws the train in plan view along the platform edge, each carriage in the place it will stop, with the zone letters beneath it. Carriages are published front to back and never sorted by availability, so the layout holds no ordering a passenger could read as a ranking. A seat whose sensor has stopped reporting is shown as unknown rather than free, and a carriage holding any unknown seat states only what it can evidence, as “at least 3 free, 7 of 108 seats unknown”. Below a fifth of the train's seats free, the screen stops grading carriages by seat count altogether and shows one instruction to spread out."));
children.push(p("The phone application answers one passenger at a time. It keeps the carriages within walking range of where that passenger is standing, prefers those with a confirmed free seat, and among them picks the carriage it has routed the fewest passengers to so far. Because it records each answer, two people standing side by side are given different carriages and the crowd divides itself before the train arrives."));
children.push(...figure("platform_map.png", "Figure 2. The platform entrance screen. Each carriage is drawn where it will stop, with its own count and zone letter. Nothing is ranked and no carriage is named.", 5.0));
children.push(h2("Bibliography for this section"));
children.push(p("Sensor and microcontroller: [1] Sharp GP2Y0A21YK0F datasheet; [2] Espressif ESP32 series datasheet. Algorithms: [3] Tukey, Exploratory Data Analysis (1977), for the running median; [4] Schmitt, A thermionic trigger, Journal of Scientific Instruments 15 (1938), for two-threshold hysteresis; [5] Ross, Introduction to Probability Models, for the Poisson process and its thinning property, used in Section 5. Full entries are in the References."));

// --------------------------------------------------------------- simulation
children.push(h1("Simulation description"));
children.push(p("Sensing a free seat is the easy half of this project. The half that carries the claim is whether telling passengers about it shortens boarding, and the prototype cannot answer that, so it is answered by simulation. Passengers arrive at a station as a Poisson process and each chooses a carriage independently; because the choices are independent, the thinning property makes the number boarding each carriage Poisson as well, with a mean equal to the arrival rate times that carriage's share [5]. The model never draws a per-carriage Poisson variable directly, so this is a property that emerges rather than one built in. Dwell follows the standard formulation [6][7]: a fixed term, a term per alighting passenger and a term per boarding passenger with a crowding penalty, taken at the busiest door rather than averaged. The generic experiments use one twelve-carriage train of 108 seats a carriage over 500 simulated stops."));
children.push(rich([
  { t: "What guidance changes is not the shape of the distribution but its means. ", b: true },
  { t: "Without guidance those means are bunched around the platform access points. With the display, the passengers who act on it choose again among the carriages within reach, weighted by the free seats each is showing. That pushes the means towards uniform: the busiest carriage, measured against the average carriage, falls from 1.89 to 1.37, where 1.00 would be perfectly uniform." },
]));
children.push(...figure("boarding_distribution.png", "Figure 3. Passengers boarding each carriage, averaged over 500 simulated stops. “With the display” is one shared platform screen showing each carriage's own free-seat count, read by 60 percent of passengers.", 4.7));
children.push(p("The share of passengers who act on the display is one parameter; what they then do is a separate one, and the second matters more. Two designs were compared at the same 60 percent compliance: the one demonstrated at the end of stage 2, which ranked the carriages and named the best three, and the positional map built for stage 3."));
children.push(spacer(80));
children.push(table(
  ["Design", "Mean dwell", "Against no display", "Busiest door", "Busiest / average"],
  [["Nothing", "142.7 s", "—", "39", "1.89"],
   ["Stage 2: name the three best carriages", "200.9 s", "41% slower", "76", "1.58"],
   ["Stage 3: each carriage shows its own state", "110.8 s", "22% faster", "33", "1.37"]],
  [3400, 1500, 1800, 1300, 1360]));
children.push(spacer(100));
children.push(rich([
  { t: "The stage 2 design does make the distribution more uniform, and still makes boarding slower. ", b: true },
  { t: "It pulls the busiest-to-average ratio from 1.89 down to 1.58, so passengers really are spread more evenly than with no display. Dwell nevertheless rises from 143 to 201 seconds. The averages improve because the three named carriages change from stop to stop, so over many stops every carriage takes a turn; within any single stop the crowd is in one place, because everybody reads the same three names at the same moment and walks to the same three doors. The busiest door nearly doubles, from 39 to 76. Dwell is set by that door at every stop and never by the long-run average, which is why a more uniform average can accompany a worse journey. That is what ended the stage 2 approach." },
]));
children.push(...figure("dwell_vs_compliance.png", "Figure 4. Dwell time against the share of passengers who act on the display, from nobody to everybody, under the two designs. Which rule the display implements matters more than how many passengers follow it.", 4.7));
children.push(p("Under the stage 3 rule most of the benefit arrives early: going from nobody to thirty percent compliance captures 25 of the eventual 35 seconds, so the system does not depend on universal compliance. Under the stage 2 rule the curve turns the other way once more than about a quarter of passengers obey it, because the more people act on a shared recommendation the harder they converge."));
children.push(h2("When seats run short"));
children.push(p("Free seats are only a proxy for where there is room, and the proxy breaks down on a nearly full train. Re-running the model at a crush operating point, where about 12 percent of the train’s seats are free at the doors and every stop falls below the 20 percent threshold, shows what happens to a display that still grades carriages by their seat counts:"));
children.push(spacer(80));
children.push(table(
  ["At a crush load, 12% of seats free", "Mean dwell", "Against no display"],
  [["Nothing", "146.0 s", "\u2014"],
   ["Grade the carriages by free seats", "161.6 s", "11% slower"],
   ["Stop grading, show one instruction to spread out", "148.4 s", "2% slower"]],
  [4600, 2200, 2560]));
children.push(spacer(100));
children.push(p("With so few seats left, the counts are small, noisy and nearly equal, and grading them funnels everyone into the two or three carriages that still have any: the display becomes 11 percent worse than showing nothing. Switching the screen to a single instruction to spread out recovers 13 of those 16 seconds. That is the fallback described in Section 4, and this is the measurement behind it. Appendix C sets out the rest of the simulation: the walking-time assumption and its lead-time requirement, what happens when the display cannot foresee who is about to alight, the per-person application measured on its own, and the remaining figures."));

// -------------------------------------------------------------- conclusions
children.push(h1("Conclusions"));
children.push(p("The sensing chain works. An infrared sensor above a seat, a calibrated relative threshold, a median filter and a one-second confirmation produce a stable occupied or empty decision in about 1.5 seconds, and the per-carriage aggregation and both passenger interfaces are built and demonstrable on a laptop. The simulation then answers the project's central question affirmatively, with two qualifications more useful than the headline: a positional map read by 60 percent of passengers cuts mean dwell by 22 percent, the application and the screen together reach 32 percent, and most of that benefit arrives by the time thirty percent of passengers act on it."));
children.push(p("The first qualification is that a display naming the best carriages makes boarding worse than no display at all, by about two-fifths, even though it flattens the long-run distribution. Showing each carriage's own state and letting passengers choose locally is what produces the benefit, so the passenger display was rebuilt as a positional map and the banner and badges were removed from it. The second is that free seats are only a proxy for where there is room, and on a nearly full train that proxy breaks down: at a crush load, grading carriages by seat count is 11 percent slower than showing nothing, which is why the screen falls back to a single instruction to spread out below a fifth of seats free. At the crush loads where this system would matter most, the right measurement is crowding rather than seats."));
children.push(p("What remains is to replace assumptions with measurements: a platform count of boarders per carriage, a stopwatch survey of dwell times, and a compliance estimate from showing the display to real passengers. The wireless train-to-platform link and the platform display hardware remain to be chosen, and are the decisions that gate a deployment."));

// ================================================================ appendices
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Appendix A — User guide for the simulation"));
children.push(p("The simulation is a command-line program. It needs Python 3.10 or later with numpy and matplotlib installed."));
children.push(code("pip install numpy matplotlib"));
children.push(h2("Running it"));
children.push(p("From the simulation folder, the comparison and all charts:"));
children.push(code("python boarding_sim.py"));
children.push(h2("Options worth changing"));
children.push(table(
  ["Option", "Default", "What it changes"],
  [["--compliance", "0.6", "Share of passengers who act on the display"],
   ["--strategy", "proportional / adaptive", "What a passenger who follows the display does"],
   ["--stops", "500", "Simulated station stops per scenario"],
   ["--arrivals", "240", "Mean passengers boarding per stop"],
   ["--t-board", "1.5", "Seconds per boarding passenger at one door"],
   ["--seed", "12345", "Random seed; the same seed reproduces a run exactly"],
   ["--no-charts", "off", "Print the numbers without drawing figures"]],
  [2400, 2200, 4760]));
children.push(spacer(100));
children.push(h2("What it produces"));
children.push(p("Everything is written to the results folder: summary.json with every number, boarders_per_car.csv, compliance_sweep.csv, and the figures used in this document. Running the same command twice with the same seed produces identical output."));
children.push(h2("Reading the output"));
children.push(bullet("Dwell time is the mean seconds the train stands at a station, set by its busiest door."));
children.push(bullet("Busiest door is the number of passengers boarding through the most loaded carriage; it is what dwell is driven by."));
children.push(bullet("Busiest carriage against the average is the evenness measure: 1.00 is perfectly uniform, 1.89 is the modelled situation with no display."));
children.push(bullet("Variance over mean near 1.0 confirms the per-carriage counts are Poisson, as the model's structure implies."));

children.push(h1("Appendix B — Programmer guide for the simulation"));
children.push(h2("Files"));
children.push(table(
  ["File", "Responsibility"],
  [["boarding_sim.py", "The model, the experiments and the console report"],
   ["charts.py", "Every figure; no model logic"],
   ["README.md", "Assumptions, results and sources"]],
  [2800, 6560]));
children.push(spacer(100));
children.push(h2("How one stop is simulated"));
children.push(numbered("Alighting passengers are drawn per carriage in proportion to who is aboard.", "stepsB"));
children.push(numbered("The number of waiting passengers is drawn from a Poisson distribution.", "stepsB"));
children.push(numbered("Each passenger is assigned the carriage they would naturally walk to, drawn from the baseline profile, which is a mixture of Gaussians centred on the platform access points.", "stepsB"));
children.push(numbered("A compliance share of them then act on the display, according to the chosen strategy, limited by how far they will walk.", "stepsB"));
children.push(numbered("Dwell is computed as the fixed term plus the maximum over carriages of the alighting and boarding terms.", "stepsB"));
children.push(numbered("Occupancy carries forward to the next stop.", "stepsB"));
children.push(h2("Key functions"));
children.push(table(
  ["Function", "What it does"],
  [["baseline_profile(p)", "Probability of choosing each carriage with no guidance"],
   ["choose_cars(...)", "Turns a passenger count into boarders per carriage; all behaviour rules live here"],
   ["dwell_seconds(...)", "The dwell equation, taken at the busiest door"],
   ["run(p, guided)", "One scenario over p.stops stops, with separate random streams"],
   ["compare(p)", "Paired guided and unguided comparison plus the summary numbers"],
   ["sweep_compliance(p)", "Dwell against compliance, for one behaviour rule"],
   ["compare_strategies(p)", "The behaviour rules at one compliance level"]],
  [2800, 6560]));
children.push(spacer(100));
children.push(h2("Changing the model"));
children.push(bullet("Every tunable value is a field of the Params dataclass at the top of boarding_sim.py, with a comment giving its basis."));
children.push(bullet("To add a behaviour rule, add a branch in choose_cars and a label in compare_strategies. Nothing else needs to change."));
children.push(bullet("Arrivals, alighting and behaviour draw from separate random streams, so the guided and unguided runs face the same sequence of arrivals. The comparison is paired; keep it that way when adding experiments."));

children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Appendix C — Supporting simulation detail"));
children.push(h2("Model parameters"));
children.push(table(
  ["Parameter", "Value", "Basis"],
  [["Carriages × seats", "12 × 108", "Matches the SmartRail display"],
   ["Boarding passengers per stop", "240, Poisson", "Estimate for a busy suburban stop"],
   ["Passengers acting on the display", "60%", "Unmeasured; Figure 4 sweeps it from 0 to 100%"],
   ["Furthest a passenger will walk", "3 carriages", "About 78 m, roughly 60 s on foot"],
   ["Fixed dwell term", "11.0 s", "Within the 10.4–13.5 s range reported in [7]"],
   ["Seconds per boarding passenger, per door", "1.5 s", "See the note below on per-door versus per-vehicle"],
   ["Seconds per alighting passenger, per door", "1.0 s", "Same basis"],
   ["Crowding penalty at a full carriage", "+45%", "Congestion term of the standard model [6]"],
   ["Stops simulated", "500 per scenario", "Enough for the means to settle"]],
  [3600, 1900, 3860]));
children.push(spacer(100));
children.push(rich([
  { t: "Per-door against per-vehicle rates. ", b: true },
  { t: "The published regressions give a combined boarding-and-alighting coefficient of 0.26 to 0.28 seconds per passenger [7]. That figure is per vehicle: it is fitted against the total number of passengers using the vehicle, whose doors work in parallel. This model works per door, because dwell is set by the busiest one, so its coefficient must be larger by roughly the number of door streams. At 1.5 seconds per boarding passenger per door, the implied vehicle has about five or six door streams, which is typical of the light rail vehicles those regressions were fitted on. The fixed term is quoted per vehicle in both cases, which is why 11.0 s is used directly and sits inside the reported 10.4–13.5 s range." },
]));
children.push(h2("That the per-carriage counts really are Poisson"));
children.push(p("The model draws a total and assigns passengers one at a time, so nothing forces the per-carriage counts to be Poisson. They are anyway, which is the thinning property at work [5]: over 500 stops the busiest carriage has a variance of 37.4 against a mean of 37.6, and for a Poisson variable the two are equal."));
children.push(...figure("poisson_counts.png", "Figure 5. Boarders at the busiest carriage over 500 simulated stops with no display, against the Poisson distribution with the same mean.", 5.2));
children.push(h2("Why the long-run average is the wrong measure"));
children.push(p("Dwell is set at every stop by the busiest door, so what matters is the whole spread of that number and not its average. Two consecutive stops under each design show it as boarders per carriage:"));
children.push(spacer(80));
children.push(table(
  ["Design", "Boarders per carriage at one stop", "Busiest door"],
  [["Stage 3 map", "15  26  27  24  30  20  26  13  18  16  9  3", "30"],
   ["Stage 3 map", "25  20  41  38  26  25  27  21  9  9  10  4", "41"],
   ["Stage 2 ranking", "5  10  100  11  11  7  12  5  8  55  2  1", "100"],
   ["Stage 2 ranking", "20  41  40  11  9  7  87  9  23  4  1  3", "87"]],
  [1900, 5460, 2000]));
children.push(spacer(100));
children.push(...figure("busiest_door.png", "Figure 6. Passengers boarding through the most loaded carriage at a single stop, over 500 stops, under both designs.", 5.2));
children.push(...figure("display_designs.png", "Figure 7. The same train and the same two waiting crowds under both designs. The free-seat numbers are one real moment from the simulation; the arrows show where passengers would walk, given a three-carriage limit.", 5.4));
children.push(h2("Walking is not free"));
children.push(p("The model charges nothing for the walk along the platform: it assumes a passenger reads the display while waiting, walks to the suggested carriage before the train arrives, and is standing there when the doors open. That is defensible but carries a requirement. A double-deck coach is about 26 m and a platform walking pace about 1.3 m/s, so the three-carriage limit is roughly 78 m or 60 seconds. The display must therefore show the approaching train's state at least a minute before it arrives, and the whole sensing chain has to fit inside that minute. A passenger who does not make it boards where they stand, which is arithmetically identical to not having followed the display, and the compliance sweep already covers that case."));
children.push(spacer(80));
children.push(table(
  ["Furthest a passenger will walk", "Distance", "Notice needed", "Screen", "App"],
  [["2 carriages", "52 m", "40 s", "19%", "39%"],
   ["3 carriages", "78 m", "60 s", "22%", "43%"],
   ["4 carriages", "104 m", "80 s", "25%", "45%"],
   ["6 carriages", "156 m", "120 s", "29%", "45%"]],
  [3200, 1500, 1800, 1430, 1430]));
children.push(spacer(100));
children.push(p("Even one carriage of movement and twenty seconds of notice recovers 14 percent on a screen and 32 percent through an application. The application saturates at about four carriages, because beyond that the balancing is limited by where passengers start rather than by how far they will go."));
children.push(h2("The display cannot see who is about to get off"));
children.push(p("The figures quoted so far let the display show free seats as they will be once the passengers leaving at this station have gone. No sensor can know that in advance. A waiting passenger chooses where to stand before the train arrives, so what they can actually be shown is what the sensors see on approach, with the alighting still to come. Re-running every scenario on that basis is the honest test:"));
children.push(spacer(80));
children.push(table(
  ["Design", "If the display could foresee alighting", "Sensors only"],
  [["Screen, map", "22%", "20%"],
   ["App, per-person advice", "43%", "44%"]],
  [3400, 3400, 2560]));
children.push(spacer(100));
children.push(p("The cost is two percentage points for the screen and none for the application. Passengers leaving are spread across the carriages roughly in proportion to how full each one is, so alighting changes every carriage's count in much the same direction and leaves their order largely intact. This is reassuring for a sensing system: the quantity the sensors can actually measure is good enough, and a per-station alighting prediction would be a refinement rather than a prerequisite."));
children.push(h2("The application measured on its own"));
children.push(p("A screen shows one picture to everybody, so everyone reading it works from the same data and their choices are correlated. An application can tell different passengers different things and can account for what it has already told the previous ones. Taken alone, with no platform screens at all, its benefit scales with how many people carry it:"));
children.push(spacer(80));
children.push(table(
  ["Phones with the app", "Mean dwell", "Saving", "Busiest door"],
  [["5%", "134 s", "6%", "37"],
   ["10%", "127 s", "11%", "36"],
   ["20%", "112 s", "22%", "32"],
   ["30%", "98 s", "31%", "28"],
   ["50%", "84 s", "41%", "23"],
   ["70%", "79 s", "45%", "21"],
   ["100%", "78 s", "45%", "21"]],
  [2600, 2400, 2200, 2160]));
children.push(spacer(100));
children.push(p("The benefit saturates near 70 percent, beyond which the walking limit rather than the advice constrains the spreading. A realistic application reach of 10 to 20 percent sits at the lower end, saving 11 to 22 percent on its own, which is why the platform screen remains worth building alongside it. Combining the two gives 32 percent, against 22 percent for either alone."));
children.push(h2("How much to trust these numbers"));
children.push(p("The percentage saving is robust to the parameter most likely to be wrong: across boarding rates from 0.8 to 2.5 seconds per passenger the saving stays between 21 and 23 percent, because the guided and unguided cases scale together. The absolute saving in seconds is not robust, and neither is anything that depends on how passengers bunch today. Three measurements would turn this from a plausible model into evidence: counting boarders per carriage on a real platform, timing thirty to forty stops, and showing the display to passengers to estimate compliance."));

// ------------------------------------------------------- stage 2 appendices
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Appendix D — Stage 2 programmer guide"));
children.push(rich([{ t: "Reproduced from Presentation/PROGRAMMER_MANUAL.md in the project repository as submitted for stage 2. Stage 3 superseded the recommendation policy described in it; Sections 4 and 5 of this document describe what replaced it.", i: true, c: MUTE }], { size: 18, after: 160 }));
children.push(new Paragraph({ spacing: { after: 160 }, children: [
  new ExternalHyperlink({ children: [new TextRun({ text: "https://github.com/abedazem13/SmartRail",
    size: BODY, color: "1D4ED8", underline: {}, font: "Calibri" })],
    link: "https://github.com/abedazem13/SmartRail" })] }));
children.push(...markdown("PROGRAMMER_MANUAL.md"));

children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Appendix E — Stage 2 user guide"));
children.push(rich([{ t: "Reproduced from Presentation/USER_MANUAL.md in the project repository as submitted for stage 2.", i: true, c: MUTE }], { size: 18, after: 160 }));
children.push(...markdown("USER_MANUAL.md"));

// ------------------------------------------------------------------ sources
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("References"));
const ref = (n, text, url) => new Paragraph({
  spacing: { after: 100, line: 280 },
  indent: { left: 420, hanging: 420 },
  children: [
    new TextRun({ text: `[${n}]  `, size: 19, bold: true, color: INK, font: "Calibri" }),
    new TextRun({ text: text + (url ? " " : ""), size: 19, color: INK, font: "Calibri" }),
    ...(url ? [new ExternalHyperlink({ children: [new TextRun({ text: url, size: 17,
      color: "1D4ED8", underline: {}, font: "Calibri" })], link: url })] : []),
  ],
});
children.push(h2("Sensors and hardware"));
children.push(ref(1, "Sharp Corporation. GP2Y0A21YK0F distance measuring sensor unit, datasheet. Analogue output, 10–80 cm measuring range."));
children.push(ref(2, "Espressif Systems. ESP32 series datasheet. ADC1 and ADC2 behaviour with Wi-Fi enabled, GPIO input limits."));
children.push(h2("Algorithms"));
children.push(ref(3, "Tukey, J. W. Exploratory Data Analysis. Addison-Wesley, 1977. Running-median smoothing."));
children.push(ref(4, "Schmitt, O. H. A thermionic trigger. Journal of Scientific Instruments, 15(1), 1938, pp. 24–26. Two-threshold switching, the basis of hysteresis."));
children.push(ref(5, "Ross, S. M. Introduction to Probability Models. Academic Press. The Poisson process and its thinning property."));
children.push(h2("Dwell time"));
children.push(ref(6, "Public Transportation Systems, lecture 9: dwell-time models. MIT OpenCourseWare, Spring 2017.",
  "https://live.ocw.mit.edu/courses/1-258j-public-transportation-systems-spring-2017/79e5b6b5a78002efdf3ec1697b7573c2_MIT1_258JS17_lec09.pdf"));
children.push(ref(7, "Modelling dwell time in light rail systems: regression coefficients and fixed minimum dwell. University of Southampton.",
  "https://eprints.soton.ac.uk/414364/1/4_50.pdf"));
children.push(h2("Occupancy sensing and deployed systems"));
children.push(ref(8, "Deutsche Bahn improves regional passenger experience with real-time capacity information. Railway News.",
  "https://railway-news.com/db-improves-regional-passenger-experience-with-real-time-capacity-information"));
children.push(ref(9, "UK premiere: Arriva Rail London app from Hacon shows loadweigh information in real time, 26 September 2017. Per-carriage loading given to station staff on Class 378 units.",
  "https://www.hacon.de/en/news/press/uk-premiere-arriva-rail-london-app-from-hacon-shows-loadweigh-information-in-real-time/"));
children.push(ref(10, "VisualCounter Transit TOF: time-of-flight 3D passenger counting, manufacturer product brochure, APTA 2023. Accuracy figure is manufacturer-stated.",
  "https://www.aptaexpo.com/apta2023//custom/PDFs/APTA23PR/VisualCounter.Transit.TOF_MK-BR-030.06-EN%20(1).pdf"));
children.push(ref(11, "Madsen, T. et al. Comparison and fusion of WLAN-probe and infrared door-counter occupancy estimation on buses. Sensors, 22, 2022, article 4111.",
  "https://vbn.aau.dk/files/492069003/sensors_22_04111_v2.pdf"));
children.push(ref(12, "Evaluation of passenger counter system for an AVM experiment, volume I: technical report, 1979. Treadle-mat and infrared-beam counters compared on transit buses.",
  "https://trid.trb.org/View/88777"));
children.push(h2("Project repository"));
children.push(ref(13, "SmartRail: firmware, PC software, simulation and documentation.",
  "https://github.com/abedazem13/SmartRail"));

// ------------------------------------------------------------------- doc ---
const listLevel = (ref, format, text) => ({
  reference: ref,
  levels: [{ level: 0, format, text, alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 420, hanging: 240 } } } }],
});

const doc = new Document({
  creator: "Yazan Rabea, Abed Azem, Samar Khatib",
  title: "SmartRail — Research Document, stage 3",
  numbering: { config: [
    listLevel("bullets", LevelFormat.BULLET, "•"),
    // Each numbered list gets its own reference so it starts again at 1.
    listLevel("numbers", LevelFormat.DECIMAL, "%1."),
    listLevel("proj", LevelFormat.DECIMAL, "%1."),
    listLevel("stepsB", LevelFormat.DECIMAL, "%1."),
  ] },
  sections: [{
    properties: { page: { margin: { top: 1300, bottom: 1300, left: 1300, right: 1300 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(process.env.SMARTRAIL_OUT || "./SmartRail_Report.docx", b);
  console.log("written");
});
