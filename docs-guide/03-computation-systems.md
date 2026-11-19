# Computation systems

Traditional pañcāṅga computation has several genuinely contested conventions — which
ayanāṃśa (sidereal zero-point) to use, whether a lunar month ends at the new moon
(amānta) or full moon (pūrṇimānta), how an intercalary (adhika) month is detected. Rather
than pick one, jyotisha bundles each full combination of choices into a
`ComputationSystem`, and you pass one in whenever you compute a pañcāṅga.

## The presets

`jyotisha.panchaanga.temporal.ComputationSystem` ships several ready-made instances as
class attributes (see `jyotisha/panchaanga/temporal/__init__.py`):

| Constant | Month assignment | Ayanāṃśa |
|---|---|---|
| `MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180` (= `DEFAULT`) | amānta, multi-new-moon adhika detection | Citrā-at-180° |
| `MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_PURNIMANTA__CHITRA_180` | pūrṇimānta | Citrā-at-180° |
| `MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180` | month ends at full moon | Citrā-at-180° |
| `MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__RP` | amānta | Rāṣṭrīya Pañcāṅga (govt. of India) nakṣatra tracking |
| `SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180` | solstice-anchored adhika rule | Citrā-at-180° |
| `SOLSTICE_POST_DARK_10_ADHIKA__RP` | solstice-anchored adhika rule | Rāṣṭrīya Pañcāṅga |

If you don't pass a `computation_system`, `DailyPanchaanga`/`annual.*` default to
`ComputationSystem.DEFAULT`.

## Ayanāṃśa actually changes the sidereal position

```python
from jyotisha.panchaanga.spatio_temporal import City, daily
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac import AngaType
from indic_transliteration import sanscript

city = City.get_city_from_db("Chennai")
d = Date(2024, 1, 15)

for label, cs in [
    ("Citrā-at-180°", ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180),
    ("Rāṣṭrīya Pañcāṅga", ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__RP),
]:
    p = daily.DailyPanchaanga(city=city, date=d, computation_system=cs)
    print(label, "->", p.sunrise_day_angas.get_anga_data_md(
        anga_type=AngaType.NAKSHATRA, script=sanscript.DEVANAGARI, reference_jd=p.julian_day_start))
```

```
Citrā-at-180° -> **नक्षत्रम्** — शतभिषक्►08:05; पूर्वप्रोष्ठपदा►30:08!; उत्तरप्रोष्ठपदा►
Rāṣṭrīya Pañcāṅga -> **नक्षत्रम्** — शतभिषक्►08:07; पूर्वप्रोष्ठपदा►30:10!; उत्तरप्रोष्ठपदा►
```

Same nakṣatra, slightly different boundary time (a couple of minutes) — the two
ayanāṃśas differ by a fraction of a degree, which is enough to shift precise transition
times without (usually) changing which nakṣatra/tithi is reported.

## Amānta vs. pūrṇimānta actually changes the month number

This is the more consequential knob — the two conventions can disagree on *which*
lunar month a given day belongs to for roughly half of every month:

```python
for label, cs in [
    ("AMAANTA", ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180),
    ("PURNIMANTA", ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_PURNIMANTA__CHITRA_180),
]:
    for dd in [Date(2024, 1, 15), Date(2024, 1, 26)]:
        p = daily.DailyPanchaanga(city=city, date=dd, computation_system=cs)
        print(label, dd, "-> lunar month index:", p.lunar_date.month.index)
```

```
AMAANTA 2024-01-15 -> lunar month index: 10
AMAANTA 2024-01-26 -> lunar month index: 10
PURNIMANTA 2024-01-15 -> lunar month index: 10
PURNIMANTA 2024-01-26 -> lunar month index: 11
```

2024-01-25 was a full moon. Pūrṇimānta rolls the month number over right after the full
moon (so by Jan 26 it's already month 11); amānta doesn't roll over until the *next* new
moon (mid-February), so it's still reporting month 10 on Jan 26. If you build any
UI/report that mixes month numbers from two different `ComputationSystem`s, they will
disagree for roughly two weeks out of every month — this is expected, not a bug.

## Festival options

`ComputationSystem.festival_options` (a `FestivalOptions` instance) controls which
festival rule repositories get consulted and a few festival-adjacent behaviors:

```python
from jyotisha.panchaanga.temporal import FestivalOptions

opts = FestivalOptions()
print(len(opts.repos))                 # 64 repos by default (everything under
                                        # jyotisha/panchaanga/temporal/festival/data)
print(opts.no_fests)                   # None (falsy) -> festivals enabled
print(opts.aparaahna_as_second_half)   # False
```

Useful fields:
- `no_fests=True` — skip festival computation entirely (much faster; several presets
  above, e.g. the pūrṇimānta/full-moon ones, set this because their festival timing
  hasn't been ported yet — see the `TODO` comments in `ComputationSystem`'s source).
- `fest_repos` / `fest_repos_excluded_patterns` — restrict to (or exclude) specific
  repositories, e.g. if you only care about `tamil` festivals and not every temple's
  local calendar. See [06-festivals.md](06-festivals.md) for what a "repository" is.
- `fest_id_patterns_excluded` — regex-exclude specific festival IDs.

### Pitfall: `no_fests=True` doesn't mean "empty repo list"

`ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_PURNIMANTA__CHITRA_180` sets
`festival_options=FestivalOptions(no_fests=True)` but its `repos` list is still populated
(via `init_repos()`, which runs unconditionally in `FestivalOptions.__init__`). If you're
inspecting a `ComputationSystem` to figure out "will this produce festivals", check
`no_fests`, not whether `repos` is empty.
