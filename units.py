"""Display units.

The solver works in internal grid units (≈1 per aisle cell). For a realistic,
store-like presentation we convert those to **metres** and **minutes**:

- one grid edge ≈ 5 m of walking,
- internal time is scaled to minutes (the congested core is genuinely slower,
  so a route through it can take a few extra minutes — e.g. waiting behind
  other shoppers — even if it is shorter in metres).

Scaling is linear, so it never changes which routes are Pareto-optimal; it only
makes the numbers on screen believable.
"""

METERS_PER_UNIT = 5.0     # metres per internal distance unit (one aisle cell)
MIN_PER_UNIT = 0.10       # minutes per internal time unit


def meters(distance):
    return distance * METERS_PER_UNIT


def minutes(time):
    return time * MIN_PER_UNIT
