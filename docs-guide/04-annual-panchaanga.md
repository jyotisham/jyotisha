# Computing a full year

## Basic call

```python
import logging, time
logging.disable(logging.CRITICAL)

from jyotisha.panchaanga.spatio_temporal import City, annual
from jyotisha.panchaanga.temporal import ComputationSystem

city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")

t0 = time.time()
panchaanga = annual.get_panchaanga_for_civil_year(
    city=city, year=2024, computation_system=ComputationSystem.DEFAULT, allow_precomputed=False)
print(time.time() - t0)  # ~27s on a modern laptop, with the full default festival rule set
```

This returns a `jyotisha.panchaanga.spatio_temporal.periodical.Panchaanga` — not a
`DailyPanchaanga` — holding a full year (plus padding days, see below) of daily data and
a festival index built by cross-referencing all of them.

### Pitfall: this is slow, and it silently reads/writes a cache directory

`get_panchaanga_for_civil_year` (and its Kali-year / Śaka-year siblings) default to
`allow_precomputed=True`, `precomputed_json_dir="~/Documents/jyotisha"`. That means:

- By default, calling this function checks
  `~/Documents/jyotisha/<city>__gregorian_<year>__<computation_system repr>.json` first,
  and only recomputes if that file is missing.
- Even when you pass `allow_precomputed=False` to force a fresh computation, the result
  still gets **written** to that same path afterward — so a second call (even with
  `allow_precomputed=False`) will find a same-named file sitting there from a previous
  run if you're not careful about cleanup, though it won't be read unless
  `allow_precomputed=True`.
- Full multi-year recomputation (used in some of this repo's own manual/regression
  tests) takes 7-11+ minutes per year — see `jyotisha_manual_tests/README.md`. A single
  civil year with the default rule set is much cheaper (tens of seconds, as timed
  above), but still not "interactive" if you're doing this inside a web request.
- If you don't want jyotisha writing files under your home directory at all, pass an
  explicit `precomputed_json_dir` you control, or load/save `Panchaanga.dump_to_file` /
  `Panchaanga.read_from_file` yourself.

For experimenting with this guide's examples without waiting, this repo ships a
pre-computed fixture you can load instantly:

```python
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga

panchaanga = Panchaanga.read_from_file(
    filename="jyotisha_tests/spatio_temporal/data/Chennai-2019.json")
```

## Iterating over days

```python
days = panchaanga.daily_panchaangas_sorted()
print(len(days))                        # 397 for a civil year — see padding note below
print(panchaanga.duration_prior_padding)  # 2

for dp in days[:3]:
    print(dp.date, dp.lunar_date.month.index)
```

### Pitfall: the day list has padding at both ends

`daily_panchaangas_sorted()` doesn't return exactly Jan 1 – Dec 31 (365/366 days) — it
includes a few extra days *before* Jan 1 and *after* Dec 31
(`panchaanga.duration_prior_padding`, e.g. `2`), because computing month/tithi
transitions correctly near the year boundary requires looking slightly outside it. If
you're slicing `daily_panchaangas_sorted()` by a fixed day-of-year offset (as this
repo's own tests do, e.g. `jyotisha_tests/spatio_temporal/test_annual.py`'s
`test_adhika_maasa_computations_2009`), always add `duration_prior_padding` to your
offset, or you'll be off by a few days.

## Adhika (intercalary) months

When a lunar month doesn't contain a solar month transition (saṅkrānti), it's repeated —
marked with a `.5` on the month index. This is directly observable:

```python
computation_system = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180
# 2018 had an adhika month (adhika jyeṣṭha):
months_2018 = [d.lunar_date.month.index for d in
               panchaanga.daily_panchaangas_sorted()[panchaanga.duration_prior_padding + 134:
                                                       panchaanga.duration_prior_padding + 195]]
# -> [2, 2.5, 2.5, ..., 2.5 (29 times), 3, 3, ..., 3 (30 times), 4]
```

(See `jyotisha_tests/spatio_temporal/test_annual.py::test_adhika_maasa_computations_2018`
for the full verified sequence — `2` for one day, then `2.5` repeated 29 times, `3` for
30 days, then `4`.) If your code assumes month index is always a plain integer 1-12
(e.g. using it as a list index or dict key typed as `int`), an adhika month will produce
`2.5` and break that assumption.

## Finding festivals

A `Panchaanga`'s `festival_id_to_days` maps every festival id observed in the period to
the *set* of civil dates it fell on (usually one date, sometimes more for
multi-day/recurring observances):

```python
print(len(panchaanga.festival_id_to_days))  # 1534 distinct festival ids for 2024, default options

for fest_id, days in panchaanga.festival_id_to_days.items():
    if fest_id == "zrIvinAyaka-caturthI":
        print(fest_id, days)  # {2019-09-02} (for the Chennai-2019 fixture)
```

Per-day, `DailyPanchaanga.festival_id_to_instance` (populated only when the day came
from an annual/periodical computation, unlike a lone `DailyPanchaanga` — see
[02-quickstart.md](02-quickstart.md)) gives you the festivals landing on *that* specific
day:

```python
from jyotisha.panchaanga.temporal.time import Date

dp = panchaanga.daily_panchaanga_for_date(Date(2019, 9, 2))
print(list(dp.festival_id_to_instance.keys()))
# ['anadhyAyaH~sAmavEda-upAkarma~2', 'sOmacitrA-naktavrata-yOgaH',
#  'tiruccendUr_murugan2_AvaNit_tiruvizhA_##10##m_nAL—tEr',
#  'zrIvinAyaka-caturthI', 'zukla-caturthI-vratam']
```

Note `festival_id_to_days` maps to a `set`, not a `list` — if you need a stable order for
serialization or display, sort it explicitly (jyotisha's own tests do this too, converting
to sorted lists before comparing JSON fixtures — see the comment in
`jyotisha_tests/spatio_temporal/test_annual.py::panchaanga_json_comparer`).
