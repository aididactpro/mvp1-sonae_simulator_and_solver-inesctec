# Roadmap & improvement ideas

Internal notes (not shown in the app) — suggestions for improving the
multi-objective picking planner for public (learner) and academic (research) use.

## For public / learners — UX
- **Onboarding tour.** A one-time guided overlay (highlight the front, then the map)
  instead of a wall of text.
- **Plain-language toggle.** Hide jargon by default; reveal "researcher mode" terms on demand.
- **Live linked highlighting.** Hovering a Pareto point pulses the matching route on the map
  (and vice-versa). Currently selection is click-only.
- **Narrated comparison.** Auto-generate "this route saves X min for Y m extra" for the
  selected point, not just in the beginner assignment.
- **Accessibility.** Colour-blind-safe palette option, larger hit targets, keyboard navigation.
- **Mobile layout.** The two-column map + front does not reflow well on phones.

## For researchers / academic — features
- **Quality indicators.** Report hypervolume and IGD+ (via `moocore`) and plot convergence
  over iterations, not just point counts.
- **Algorithm comparison.** Run BicriterionAnt / MACS / NSGA-II side by side on one instance.
- **Constraints.** Honour precedence, first/last product, fresh/frozen-last and queue waits
  inside the multi-objective search (current version is source → checkout + list only).
- **Real path-level trade-offs.** Expose the per-leg bi-objective path options explicitly.
- **Batch experiments & export.** Multi-seed runs, CSV/JSON export of fronts, reproducible configs.
- **Bring-your-own instance.** Upload a store graph / product map.

## Technical / modelling
- The **congestion time model** is an illustrative assumption, not measured data — make it
  swappable for real walking-time / dwell-time observations.
- mACO1 parameters are exposed but not auto-tuned; an `irace`-style tuner would help.
- Brute-force exact-front check only runs for small instances (≤ 7 stops).
- Caching keys on the shopping list + params; changing the congestion model needs a cache reset.
