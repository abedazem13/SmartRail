"""Charts for the SmartRail boarding simulation."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INK, MUTE = "#0F172A", "#64748B"
GREY, GREEN, RED = "#CBD5E1", "#16A34A", "#DC2626"
GRID = "#E2E8F0"


def _frame(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=34, fontweight="bold", color=INK, pad=20, loc="left")
    ax.set_xlabel(xlabel, fontsize=24, color=INK)
    ax.set_ylabel(ylabel, fontsize=24, color=INK)
    ax.tick_params(labelsize=24, colors=INK, length=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(MUTE)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)


def _note(fig, text):
    fig.text(0.012, 0.045, text, fontsize=20, color=MUTE, linespacing=1.6, va="bottom")


def distribution(p, res, path):
    """Boarders per carriage: bunched versus flattened, against uniform."""
    cars = np.arange(1, p.cars + 1)
    base = res["baseline"]["per_car_mean"]
    app = res["app"]["per_car_mean"]
    uniform = base.mean()

    fig, ax = plt.subplots(figsize=(19, 10), dpi=100)
    ax.bar(cars - 0.19, base, width=0.38, color=GREY, label="No guidance")
    ax.bar(cars + 0.19, app, width=0.38, color=GREEN, label="With the display")
    ax.axhline(uniform, color=INK, lw=2.5, ls="--")
    ax.text(p.cars + 0.55, uniform + 0.6, "uniform", fontsize=22, color=INK,
            va="bottom", ha="center", fontweight="bold")

    _frame(ax, "Passengers boarding each carriage, averaged over "
               f"{p.stops} simulated stops", "Carriage", "Passengers boarding")
    ax.set_xticks(cars)
    ax.set_xlim(0.3, p.cars + 1.5)
    ax.legend(fontsize=24, frameon=False, loc="upper right")
    fig.subplots_adjust(left=0.065, right=0.985, top=0.87, bottom=0.235)

    eb = base.max() / uniform
    ea = app.max() / uniform
    _note(fig, "Counts at every carriage are Poisson in both cases; guidance changes the means, not the "
               "shape of the distribution.\n"
               f"Busiest carriage against the average: {eb:.2f} without guidance, {ea:.2f} with it "
               "(1.00 would be perfectly uniform).")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def dwell_vs_compliance(p, res, comp, comp_alt, path):
    """The answer: dwell time against how many passengers follow the display."""
    x = [100 * r["compliance"] for r in comp]
    y = [r["dwell_s"] for r in comp]
    baseline = res["summary"]["dwell_baseline_s"]

    fig, ax = plt.subplots(figsize=(19, 10), dpi=100)
    ax.axhline(baseline, color=RED, lw=4, ls="--")
    ax.text(1.5, baseline + 0.35, f"No guidance: {baseline:.1f} s",
            fontsize=24, color=RED, fontweight="bold", va="bottom")
    y_alt = [r["dwell_s"] for r in comp_alt]
    # Labelled in a legend rather than beside the last point, so the axis can
    # stop at 100%: a share of passengers cannot exceed that.
    ax.plot(x, y_alt, lw=5, color=RED, marker="s", ms=11, zorder=3,
            label="Stage 2: display names the three best carriages")
    ax.plot(x, y, lw=5, color=GREEN, marker="o", ms=12, zorder=4,
            label="Stage 3: every carriage shows its own state")

    _frame(ax, "Dwell time against the share of passengers who follow the display",
           "Passengers who follow the display (%)", "Mean dwell time (s)")
    ax.set_xlim(-2, 103)
    ax.legend(fontsize=22, frameon=False, loc="upper right")
    fig.subplots_adjust(left=0.07, right=0.985, top=0.87, bottom=0.235)
    _note(fig, f"Every point is {p.stops} simulated stops, {p.arrivals:.0f} boarding passengers per stop. "
               "Dwell is set by the busiest door.\n"
               "Following the display only helps if the display spreads people out. Naming the best carriages "
               "moves the crowd together instead.")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def poisson_fit(p, res, path):
    """Evidence that the per-carriage counts are Poisson."""
    from math import exp, lgamma

    car = int(np.argmax(res["baseline"]["per_car_mean"]))
    counts = res["baseline"]["boarders"][:, car]
    lam = counts.mean()
    lo, hi = counts.min(), counts.max()
    bins = np.arange(lo - 0.5, hi + 1.5)
    k = np.arange(lo, hi + 1)
    pmf = np.exp(k * np.log(lam) - lam - np.array([lgamma(i + 1) for i in k]))

    fig, ax = plt.subplots(figsize=(19, 10), dpi=100)
    ax.hist(counts, bins=bins, density=True, color=GREY, label="Simulated stops")
    ax.plot(k, pmf, lw=5, color=GREEN, marker="o", ms=10,
            label=f"Poisson, mean {lam:.1f}")
    _frame(ax, f"Boarders at carriage {car + 1}, stop by stop",
           "Passengers boarding that carriage at one stop", "Share of stops")
    ax.legend(fontsize=24, frameon=False)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.87, bottom=0.235)
    var = counts.var(ddof=1)
    _note(fig, "Passengers arrive as a Poisson process and choose independently, so each carriage's count "
               "is Poisson too (thinning).\n"
               f"For this carriage the variance is {var:.1f} against a mean of {lam:.1f}; "
               "they match, as a Poisson variable requires.")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def strategies(p, strat, path):
    """What you tell people matters as much as how many of them listen."""
    labels = [r["strategy"] for r in strat]
    vals = [r["dwell_s"] for r in strat]
    base = vals[0]
    colors = [GREY] + [GREEN if v < base else RED for v in vals[1:]]

    fig, ax = plt.subplots(figsize=(19, 10), dpi=100)
    bars = ax.barh(range(len(labels)), vals, color=colors, height=0.6)
    ax.invert_yaxis()
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=24)
    ax.axvline(base, color=INK, lw=2.5, ls="--")
    for i, (b, r) in enumerate(zip(bars, strat)):
        if i == 0:
            tag = ""
        else:
            word = "faster" if r["saving_pct"] > 0 else "slower"
            tag = f"   {abs(r['saving_pct']):.0f}% {word}"
        ax.text(b.get_width() + 3.5, i, f"{r['dwell_s']:.0f} s{tag}",
                va="center", fontsize=24,
                color=GREEN if i and r["saving_pct"] > 0 else (RED if i else INK),
                fontweight="bold" if i else "normal")

    _frame(ax, "Dwell time under four kinds of advice", "Mean dwell time (s)", "")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, lw=1)
    ax.set_xlim(0, max(vals) * 1.38)
    fig.subplots_adjust(left=0.27, right=0.985, top=0.87, bottom=0.27)
    _note(fig, f"All four at {p.compliance:.0%} compliance. Sending everyone to the single emptiest "
               "carriage makes the crowd move together\ninstead of spreading, so the busiest door gets "
               "worse than with no guidance at all.")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def make_all(p, res, comp, comp_alt, strat, outdir):
    os.makedirs(outdir, exist_ok=True)
    distribution(p, res, os.path.join(outdir, "boarding_distribution.png"))
    dwell_vs_compliance(p, res, comp, comp_alt,
                        os.path.join(outdir, "dwell_vs_compliance.png"))
    poisson_fit(p, res, os.path.join(outdir, "poisson_counts.png"))
    strategies(p, strat, os.path.join(outdir, "guidance_strategies.png"))


def israel_journey(names, base, app, scheduled, path):
    """Dwell at each station of a real line, with and without the display."""
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(19, 10), dpi=100)
    ax.bar(x - 0.2, base["dwell"], width=0.4, color=GREY, label="Modelled: no display")
    ax.bar(x + 0.2, app["dwell"], width=0.4, color=GREEN, label="Modelled: with display")
    ax.axhline(scheduled, color=RED, lw=3, ls="--")
    ax.text(6.15, scheduled + 4, f"assumed {scheduled} s", fontsize=20,
            color=RED, fontweight="bold", ha="center", va="bottom")

    _frame(ax, "Modelled time standing at each station, Haifa to Tel Aviv",
           "", "Dwell time (s)")
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("Tel Aviv ", "TA ").replace("Haifa-", "")
                        for n in names], rotation=28, ha="right", fontsize=21)
    ax.legend(fontsize=24, frameon=False, loc="upper center", ncol=2)
    saved = base["dwell"].sum() - app["dwell"].sum()
    fig.subplots_adjust(left=0.07, right=0.985, top=0.87, bottom=0.37)
    _note(fig, "Every bar is computed from the dwell equation, not measured. Israel Railways publishes "
               "no dwell times.\n"
               "The line, stations and train are real; the passenger counts and rate constants are "
               "assumptions.\n"
               f"Journey total {base['dwell'].sum()/60:.1f} min without the display, "
               f"{app['dwell'].sum()/60:.1f} min with it: {saved:.0f} s recovered.")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def busiest_door_spread(p, runs, path, note=None):
    """Why a uniform-looking average can still be bad: the per-stop picture.

    `runs` is [(label, colour_key, result)] with colour_key in {grey, green, red}.
    """
    colours = {"grey": GREY, "green": GREEN, "red": RED}
    fig, ax = plt.subplots(figsize=(19, 10), dpi=100)
    hi = max(r["busiest"].max() for _, _, r in runs)
    bins = np.arange(0, hi + 6, 4)
    for label, key, r in runs:
        ax.hist(r["busiest"], bins=bins, density=True, histtype="step",
                lw=5, color=colours[key], label=label)
    _frame(ax, "Passengers at the busiest door, stop by stop",
           "Passengers boarding through the most loaded carriage at one stop",
           "Share of stops")
    ax.legend(fontsize=23, frameon=False, loc="upper right")
    fig.subplots_adjust(left=0.07, right=0.985, top=0.87, bottom=0.27)
    _note(fig, note or (
        "Dwell is set at each stop by this number, so what matters is the whole spread, "
        "not its average."))
    fig.savefig(path, facecolor="white")
    plt.close(fig)
