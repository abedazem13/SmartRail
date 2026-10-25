# Passenger-facing interfaces

Two components, deliberately shaped differently, because they are read by
different numbers of people at once.

| | Phone app | Platform screen |
|---|---|---|
| Read by | one person | everybody waiting, at the same moment |
| May therefore say | "go to car H" | "this carriage has 47 free seats" |
| Must never say | — | "car H is the best choice" |
| Holds state | yes: who it has already routed where | no |
| Files | `dispatcher.py`, `passenger_web/phone.*` | `platform_view.py`, `passenger_web/platform.*` |

`guidance.py` now delegates to `dispatcher.py`, so the console tool, the
simulator and the phone app all route by the same rule and cannot drift apart.
Its public names and return shapes are unchanged and `seat_live.py` keeps
working; `tests/test_guidance.py` pins both the new behaviour and the old
call shape.

The asymmetry is the design. A single instruction is safe when it is issued to
one person and the issuer remembers it; the same instruction on a shared screen
is read by two hundred people who all walk to the same doors, and the busiest
door is what holds the train at the platform. Our own boarding model put a
ranked list of carriages 49% worse than showing nothing at all, which is why
the constraints below are enforced by tests rather than left to good intentions.

## 1. Phone app: a stateful dispatcher

`dispatcher.py`. The rule, in order:

1. keep only carriages within walking range of where the passenger is standing;
2. of those, prefer ones with a **confirmed** free seat (an unknown seat is
   never treated as free);
3. among the candidates, take the one **fewest passengers have been routed to**;
4. break ties on free seats, then walking distance, then carriage id.

Step 3 is the primary key and step 4 only breaks ties. That ordering is what
divides the crowd: the emptiest carriage wins the first passenger and loses the
second, so six people standing together are sent six different ways.

Three decisions the brief did not specify, made here and documented because
they change behaviour:

- **Assignments expire** (`hold_s`, default 180 s). Without expiry the routed
  counts accumulate every passenger who ever asked, and within minutes every
  carriage looks equally used. The counts have to describe the people currently
  waiting, not the day's traffic.
- **Requests are idempotent by ticket.** A passenger who refreshes or reopens
  the app gets the same carriage back and is not counted as a second person.
  The ticket is a random id held on the phone; the server stores no identity.
- **`reset()` on departure.** `PassengerService` watches the model's station
  counter and clears the dispatcher when the train leaves, because the next
  train's waiting crowd is a different population.

## 2. Platform screen: a positional map

`platform_view.py` builds the view model; the screen renders it unchanged.

- **Physical order, always.** Carriages are published front-to-back and never
  sorted by availability. The screen draws them as a plan view of the train
  lying along the platform edge, pinned to the zone letters painted on the
  ground. A diagram pinned to physical positions has no ordering left to give
  away, and no slot a "best carriage" badge could occupy.
- **No ranking, no badges, no naming a winner.** The banner poses a local
  question — *wait by the zone nearest you that has space* — so two people
  fifty metres apart read the same screen and walk in different directions.
- **An unresponsive sensor reads as unknown, never as free.** A carriage
  holding any unknown seat is shown as unknown and states only what it can
  prove: "At least 3 free, 7 of 108 seats unknown". The screen never displays
  more availability than it has evidence for.
- **Below 20% of seats free, grading stops.** Every carriage with room reads
  identically ("Space here"), the counts disappear, and the banner becomes a
  single instruction to spread out. Near capacity the counts are small, noisy
  and nearly equal, and grading them sends everyone chasing the same two or
  three carriages. This is the case that made a ranked list worse than nothing.

A carriage with zero free seats says **"No free seats"**, not "full": standing
room is not sensed, and a passenger may still legitimately board there.

## Where each constraint is proved

| Constraint | Test |
|---|---|
| Two passengers at one spot are split | `TestCrowdDivides` |
| Fewest-routed beats emptiest | `test_the_fewest_routed_carriage_wins_before_the_emptiest` |
| Walking range is respected | `TestWalkingRange` |
| Unknown seats are never routed on | `TestNeverRoutesOnUnknown` |
| A refresh is not a second passenger | `TestIdempotency` |
| Counts track the waiting crowd | `TestExpiryAndReset` |
| Concurrent phones stay balanced | `TestConcurrency` |
| Screen is never ordered by availability | `TestNoLeaderboard` |
| Screen never overstates availability | `TestUnknownSeats` |
| Below 20%, grading stops | `TestScarceFallback` |
| The shipped HTML/JS reintroduce neither | `TestShippedFilesHoldTheLine` |
| The old `/api/state` ranking does not leak in | `test_the_dashboards_ranking_does_not_leak_into_the_screen` |

`TestShippedFilesHoldTheLine` greps the delivered pages for `sort(`, for rank
and badge slots, and for the words a later change would most plausibly add back
("best carriage", "recommended", "emptiest"). It is the test that stops this
quietly turning back into a leaderboard.

## Running it

Standalone, without touching `dashboard.py`:

```
python passenger_routes.py
```

```
Platform screen: http://127.0.0.1:8766/platform
Phone app:       http://127.0.0.1:8766/app
```

A screen at a particular end of the platform marks its own position:
`http://127.0.0.1:8766/platform?zone=F`. Two screens at opposite ends show the
same seat counts and mark different zones, which is how a shared screen still
splits a crowd by position.

Tests, from `PC_software`:

```
python -m unittest discover -s tests -p "test_*.py" -v
```

## Adding it to the existing dashboard

Two lines in `create_app()`:

```python
from passenger_routes import PASSENGER_PATHS, register_passenger_routes   # at the top
...
    register_passenger_routes(app, state)                                 # before `return app`
```

One further line is needed in the `controls_stay_on_this_machine` guard,
because that guard currently refuses every non-GET request that did not come
from this computer, and a passenger's phone is by definition not this computer:

```python
    def controls_stay_on_this_machine():
        if request.remote_addr in ("127.0.0.1", "::1", None):
            return None
        if request.path in PASSENGER_PATHS:        # add this
            return None                            # and this
        if request.method != "GET" or request.path in ("/controls", "/api/ports"):
            ...
```

This is safe to open up and nothing else is: `/api/assign`, `/api/release` and
`/api/platform` cannot change a seat, a mode, an auto-stop interval or a serial
port. The most a stranger on the network can do through them is ask for
guidance or hand an assignment back. Everything that changes the demo stays on
the host machine.

## The retained baseline

`/` now serves the positional map. The older ranked display — the
"Most confirmed free seats: …" banner and the BEST CHOICE / GOOD CHOICE
pills — moves to `/baseline` and is **left exactly as it was**. It is the
control case the boarding model measured, and editing it would spoil the
comparison, so it is retained rather than deleted and it is the only place in
the system where a carriage is still named as a recommendation.

```
SMARTRAIL_DISPLAY=ranked      # puts the old display back at /
```

`dashboard_model.snapshot()` still computes `recommended` and `message` for
that page. The two new components never read either field:
`platform_view.build_view()` reads only the per-carriage `free`, `unknown` and
`total`, and publishes neither. `test_the_dashboards_ranking_does_not_leak_into_the_screen`
asserts that separation, so the two designs can be shown side by side at the
demo and compared honestly.
