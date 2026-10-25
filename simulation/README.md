# Simulation — does the display shorten boarding?

This answers requirement **FR-007**: compare boarding with and without the
platform display, and quantify the effect on the train's dwell time.

**Headline result (default parameters, 500 simulated stops, 60% compliance):**
mean dwell falls from **142.7 s to 110.8 s, a 22% saving**, because the busiest
door drops from 39 boarding passengers to 33.

**That result depends on what the display tells people, not only on how many
obey it.** A display that shows every carriage's own state shortens dwell. A
display that names the best carriages lengthens it, because everyone waiting
reads the same screen at the same moment and walks to the same place. The
SmartRail screen currently does both: the per-carriage cards are the safe part,
the "good choice" badges and the "most confirmed free seats" banner are not.
See *What the simulation found*.

Nothing here is measured at a real station. Every number below comes from the
model, using literature-informed parameters listed under *Assumptions*. The
one thing the simulation cannot tell you is how many passengers would really
follow the display.

## Run it

```
pip install numpy matplotlib
python boarding_sim.py                       # headline comparison, charts, CSVs
python boarding_sim.py --compliance 0.3      # if only a third of people follow it
python boarding_sim.py --strategy best       # the failure mode, see below
python boarding_sim.py --no-charts           # numbers only
```

Results are written to `results/`: `summary.json`, `boarders_per_car.csv`,
`compliance_sweep.csv` and four charts.

| File | What it does |
|---|---|
| `boarding_sim.py` | The model, the experiments and the console report |
| `charts.py` | The figures |
| `gtfs_dwell.py` | Checks whether the published timetable contains dwell at all |
| `gtfs_service.py` | Pulls a real service — station times and headways — out of the same feed |

## The model

**Arrivals are Poisson.** The number of passengers waiting at a stop is
Poisson(λ), the standard assumption for passenger arrivals at a station.

**Each carriage's count is Poisson too.** Every passenger chooses a carriage
independently, so by the thinning property of a Poisson process the number
boarding carriage *i* is itself Poisson, with mean λ·p_i. The simulation never
draws a per-carriage Poisson directly — it draws the total and assigns each
passenger — so this is a property that emerges, and
`results/poisson_counts.png` shows it holding: at carriage 3 the variance is
37.4 against a mean of 37.6.

**What guidance changes is p_i, not the shape.** With no guidance, p_i is
bunched around the platform access points — a mixture of Gaussians centred on
the entrance and the staircase. With the display, a share of passengers move
to a nearby carriage showing more free seats, which pushes p_i towards uniform
(1/12 each). The busiest-carriage-to-average ratio falls from **1.89 to 1.37**.

**Dwell is set by the busiest door.** A train cannot leave until its slowest
door is finished, so

```
door time_i = t_alight · alighters_i + t_board · boarders_i · crowding_i
dwell       = t_fixed + max over carriages (door time_i)
```

This is the standard dwell-time formulation: a fixed term plus per-passenger
boarding and alighting terms, with the train's dwell taken as the maximum over
doors, and a crowding term that lengthens boarding on a full vehicle.
Flattening p_i lowers the expected maximum, and that is the whole source of
the saving.

## What the simulation found

| Advice shown on the display | Mean dwell | Against no guidance |
|---|---|---|
| None | 142.7 s | — |
| Weight by free seats | 110.8 s | **22% faster** |
| Avoid the carriages marked full | 120.4 s | 16% faster |
| Just spread out, ignoring the counts | 121.6 s | 15% faster |
| Name the three best carriages, as the screen does now | 200.9 s | **41% slower** |
| Everyone to the single emptiest carriage | 212.6 s | **49% slower** |

Three things worth taking from this table.

**The benefit is real but it comes from spreading, not from seats.** Simply
telling people to spread out along the platform already captures 15 of the 22
percentage points. The seat counts add the rest by steering people towards the
carriages that are genuinely emptier.

**Naming the best carriages backfires, and the screen currently does it.**
Everyone waiting reads the same screen at the same moment, so naming winners
moves the crowd instead of spreading it. The busiest door grows from 39
passengers to 76 and dwell rises 41%. This is not a tie-breaking artefact:
sending people to a random badged carriage rather than the nearest still gives
24% slower, and badging 8 of the 12 carriages is still slightly worse than
showing nothing.

The reason is that the badge is *global* while the passenger's problem is
*local*. Every rule that helps — weighting by free seats, avoiding the full
ones, simply spreading out — lets a passenger weigh the carriages near where
they already stand. The recommendation does not.

**What this means for the product.** Keep the per-carriage cards, which show
each carriage's own state and let people choose locally. Treat the "good
choice #1/#2/#3" badges and the "most confirmed free seats: Car L, Car J,
Car E" banner as a design risk: if passengers act on them, the simulation says
boarding gets worse than with no display at all.

**Most of the gain arrives early.** Going from 0% to 30% compliance buys 25 s
of the eventual 35 s. The system does not need everyone to obey.

| Compliance | 0% | 10% | 20% | 30% | 50% | 100% |
|---|---|---|---|---|---|---|
| Per-carriage display | 142.0 s | 130.4 s | 123.1 s | 117.5 s | 112.2 s | 108.0 s |
| Naming the 3 best | 142.9 s | 140.3 s | 137.4 s | 145.2 s | 178.8 s | 322.6 s |

The second row is the same compliance axis under the other rule. Both are in
`results/dwell_vs_compliance.png`.

## Assumptions

Each of these is a parameter in `Params` and can be changed on the command
line or in the file.

| Parameter | Default | Basis |
|---|---|---|
| Carriages × seats | 12 × 108 | Matches `dashboard_model.py` |
| Boarding passengers per stop | 240, Poisson | A busy station; **to be checked against a real platform** |
| Alighting | 25% of seated passengers | Sets the equilibrium load at ~80 of 108 seats |
| Fixed dwell term | 11 s | Published constants for the fixed part of dwell run about 10–14 s |
| Boarding | 1.5 s per passenger per door | Within the published range; see sensitivity below |
| Alighting | 1.0 s per passenger per door | Alighting is normally faster than boarding |
| Crowding | +45% boarding time at a full carriage | Standard crowding penalty in dwell models |
| Waiting profile | Gaussians at carriages 3 and 8, σ = 1.6 carriages | **The weakest assumption — measure this** |
| Walking limit | 3 carriages | Nobody walks the length of the platform for a seat |
| What a follower does | `strategy`, default `proportional` | **The weakest behavioural assumption — the sign of the result depends on it** |

### "Compliance" and "strategy" are two different things

`compliance` is the share of passengers who act on the display at all. The
rest stand where they would have stood anyway. `strategy` is what the ones who
do act then choose:

| `strategy` | A passenger who follows the display... |
|---|---|
| `proportional` (default) | picks a carriage within 3 of where they stand, with probability proportional to its free seats |
| `avoid_full` | spreads evenly over the nearby carriages the display marks as having seats |
| `spread` | spreads evenly over the nearby carriages, ignoring the counts |
| `top3` | walks to the nearest of the three carriages the screen badges, train-wide |
| `best` | walks to the emptiest carriage within reach |

Nobody has measured which of these real passengers do. That is the main thing
an experiment with the display in front of people would settle.

**The percentage saving is robust to the boarding rate**, which is the
parameter most likely to be wrong: across 0.8–2.5 s per passenger the saving
stays between 21% and 23%, because both scenarios scale together. The absolute
saving in seconds is not robust, and neither is anything that depends on the
waiting profile.

## What the model assumes about time

**Walking is free.** The model assumes a passenger reads the display while
waiting, walks to the recommended carriage before the train arrives, and is
standing there when the doors open. Only boarding consumes dwell.

That needs lead time. A double-deck coach is about 26 m and platform walking
is about 1.3 m/s, so the default three-carriage limit is roughly 78 m or 60
seconds. **The display must show the approaching train at least a minute
before it arrives**, and the whole sensing chain has to fit inside that minute.
A passenger who does not make it boards where they stand, which is identical
to that passenger not complying, and the compliance sweep already covers it.

Short walks still pay (`--max-walk-cars`):

| Walk limit | Distance | Notice needed | Screen | App |
|---|---|---|---|---|
| 1 carriage | 26 m | 20 s | 14% | 32% |
| 3 carriages | 78 m | 60 s | 22% | 43% |
| 6 carriages | 156 m | 120 s | 29% | 45% |

**The display cannot see who is about to get off.** By default the model lets
the display show free seats after this station's alighting, which no sensor
can know in advance. `foresee_alighting=False` in `Params` re-runs everything
on what the sensors actually see on approach:

| Design | Foreseeing alighting | Sensors only |
|---|---|---|
| Screen, map | 22% | 20% |
| App, per-person | 43% | 44% |

Two points for the screen, none for the app. Alighting is spread across
carriages roughly in proportion to how full each is, so it moves every count
in the same direction and leaves their order intact. A per-station alighting
prediction would be a refinement, not a prerequisite.

## Is the app redundant if there is a platform screen?

No, provided the app does something a screen cannot. A shared screen shows one
picture to everyone, so their choices are correlated. An app can give each user
a different carriage, chosen to even out the load, taking account of what it
already told the previous user. The `personalised` strategy models that.

| How the information reaches passengers | Dwell | Against no display |
|---|---|---|
| Nothing | 143 s | — |
| Shared screen, ranked list | 213 s | 49% worse |
| Shared screen, map, 60% reach | 111 s | 22% better |
| App, per-person advice, 20% reach | 112 s | 22% better |
| Both together | 96 s | 33% better |

An app on a fifth of phones matches a screen seen by three fifths of
passengers: roughly three times the effect per person reached. The two are
complementary, and together they save a third rather than a fifth.

A sign fixed to each carriage is not a substitute for either. It is readable
only once the train has arrived, when the passenger has already chosen where
to stand and the dwell is already set.

## Where the 60-second line comes from, and how to replace it

`israel_journey.py` draws a 60-second reference line for the dwell a train is
allowed at an intermediate station. **That is our assumption, not an Israel
Railways figure** — and we checked rather than guessed that no published
figure exists.

The national GTFS feed, issued by the Ministry of Transport and covering
rail, carries an `arrival_time` and a `departure_time` for every stop, so the
difference between them would be the scheduled dwell. `gtfs_dwell.py`
downloads the feed, keeps the rail trips and compares the two at every stop:

```
python gtfs_dwell.py                   # downloads the feed, about 100 MB
python gtfs_dwell.py --zip israel.zip  # a feed already on disk
```

**Result (2026-10-24): every rail stop has arrival equal to departure.** The
timetable does not publish dwell at all; it is absorbed into the run time
between stations. That is a finding in its own right — the quantity this
project tries to reduce is not something the operator currently publishes per
station — and it means the only route to a real number is a stopwatch on a
platform.

Note that the 83-second saving does not depend on this line at all. It is the
difference between two simulated dwell times. Only the overrun figures are
measured against the 60 seconds.

## Replacing the estimated service with the real one

`gtfs_service.py` reads the same feed and extracts, for the ten modelled
stations, a morning, midday and night southbound train with its real time at
each station, plus how many southbound trains call at a chosen station in
each of those windows.

```
python gtfs_service.py                        # downloads the feed
python gtfs_service.py --zip israel.zip       # a feed already on disk
python gtfs_service.py --headway-at Herzliya  # count trains elsewhere
```

It writes `service_profile.json`, a few kilobytes, holding the real run times
and headways. Two things follow from it:

* **Run times** turn the modelled journey into the actual service, so the
  saving can be quoted as a share of a real scheduled journey rather than of
  an invented one.
* **Headways** let the busiest assumption in the model be derived rather than
  guessed. A station's annual ridership divided across the operating year and
  then by the trains per hour gives boardings per train, which replaces the
  flat 240 passengers per stop.

The station names are matched on a Hebrew fragment, listed in `STATIONS` at
the top of the script. It prints what each one matched so a wrong or
ambiguous match is visible before the results are used.

## What would make this credible

1. **Measure the waiting profile.** Stand on the platform, count how many
   passengers board each carriage, and replace the Gaussian assumption. This
   is one afternoon of work and it is the assumption the whole result rests on.
2. **Measure dwell.** Time door-open to door-close for 30–40 stops and fit
   `t_fixed`, `t_board`, `t_alight` to that line rather than to the literature.
3. **Estimate compliance.** Show the display to people and ask where they would
   stand. The model says 30% is enough for most of the benefit.

Until step 1 is done, the honest claim is: *under a plausible model of how
passengers bunch, guidance of this kind shortens dwell by about a fifth, and
the result is not sensitive to the boarding rate.*

## Sources

- [Public Transportation Systems, lecture 9 — MIT OpenCourseWare](https://live.ocw.mit.edu/courses/1-258j-public-transportation-systems-spring-2017/79e5b6b5a78002efdf3ec1697b7573c2_MIT1_258JS17_lec09.pdf) — dwell-time formulation: fixed term plus per-boarding and per-alighting terms, a crowding term, and dwell taken as the maximum over doors and cars.
- [Modelling dwell time in light rail systems (University of Southampton)](https://eprints.soton.ac.uk/414364/1/4_50.pdf) — regression on real services: a combined boarding-and-alighting coefficient of 0.26–0.28 s per passenger and a fixed minimum dwell of 10.4–13.5 s.
