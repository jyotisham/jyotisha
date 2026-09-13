# jyotisha guide

`jyotisha` is a Python library for computing pañcāṅga (Hindu luni-solar calendar) data —
sunrise/sunset, tithi, nakṣatra, yoga, karaṇa, lunar/solar months, and thousands of
festival/observance dates — for any city and date, and for rendering that data as
Markdown, ICS (calendar) files, or TeX (print-ready PDF) output.

This is a hands-on, example-driven guide. It complements (doesn't replace) the two other
doc surfaces in this repo:

- The [Hugo user guide](../hugo-source/content/software/for_users.md), published at
  [jyotisham.github.io/jyotisha](https://jyotisham.github.io/jyotisha/), which is a short
  pointer page.
- The [Sphinx API reference](../docs/) published at
  [jyotisha.readthedocs.io](https://jyotisha.readthedocs.io), which is auto-generated
  docstrings (currently has some build issues — see `docs-guide`'s own notes below where
  relevant).

Every code snippet in these pages was actually run against this checkout (verified with
the `pyswisseph`-backed venv) — none of it is guessed from reading source alone.

## Which page do I want?

| Page | What it covers |
|---|---|
| [01-installation.md](01-installation.md) | Installing jyotisha and its native `pyswisseph` dependency; a sanity-check script |
| [02-quickstart.md](02-quickstart.md) | Computing a single day's pañcāṅga for a city, and reading tithi/nakṣatra/yoga/karaṇa/sunrise off the result |
| [03-computation-systems.md](03-computation-systems.md) | The `ComputationSystem` knobs: ayanāṃśa, amānta vs. pūrṇimānta months, festival options — with side-by-side examples showing them actually changing the output |
| [04-annual-panchaanga.md](04-annual-panchaanga.md) | Computing a full year, iterating days, finding festivals across the year, adhika (leap) months, caching/performance |
| [05-writers.md](05-writers.md) | Turning a computed pañcāṅga into Markdown, an `.ics` calendar file, or TeX/PDF output |
| [06-festivals.md](06-festivals.md) | How the festival-rule data (TOML files, one per festival) is structured, how to query it, and how to add/customize a rule |

## The core mental model

1. A **`City`** (name, lat/long, timezone) plus a **`Date`** plus a **`ComputationSystem`**
   (which ayanāṃśa, which month-numbering convention, which festival rule-repos) get fed
   into `DailyPanchaanga` (one day) or `annual.get_panchaanga_for_civil_year` (a full year,
   returning a `Panchaanga` object holding 365+ `DailyPanchaanga`s plus festival indices).
2. Festival matching only happens in the **annual/periodical** computation — a lone
   `DailyPanchaanga` always has an empty `festival_id_to_instance`, because many festival
   rules need neighboring days to resolve which of two candidate days wins
   (`puurvaviddha`/`paraviddha`/`vyaapti`). See [02-quickstart.md](02-quickstart.md) and
   [06-festivals.md](06-festivals.md).
3. The computed object is a plain, JSON-(de)serializable tree (`sanskrit_data.JsonObject`
   subclasses throughout), so it can be cached to / loaded from disk instead of
   recomputed — annual computation with the full festival rule set is genuinely slow
   (tens of seconds to minutes; see [04-annual-panchaanga.md](04-annual-panchaanga.md)).
