# Quickstart: computing one day's pañcāṅga

## Pick a city

Either look one up from the bundled place database (a TSV of pre-geocoded places with
timezones):

```python
from jyotisha.panchaanga.spatio_temporal import City

city = City.get_city_from_db("Chennai")
print(city.name, city.latitude, city.longitude, city.timezone)
# Chennai 13.09 80.27 Asia/Calcutta
```

...or construct one directly with `(name, latitude, longitude, timezone)`. Lat/long can
be sexagesimal strings (`"13:05:24"`) or decimal degrees; the constructor detects which
by checking for a `:`:

```python
city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
```

Run `City.get_city_from_db(name)` with a bad name and you'll get a `KeyError` from the
underlying pandas lookup, not a friendly "city not found" — if you're accepting city
names from user input, validate against `City.get_city_df()["Name"]` first.

## Compute a day

```python
import logging
logging.disable(logging.CRITICAL)

from jyotisha.panchaanga.spatio_temporal import City, daily
from jyotisha.panchaanga.temporal.time import Date

city = City.get_city_from_db("Chennai")
panchaanga = daily.DailyPanchaanga(city=city, date=Date(2024, 1, 15))
```

`Date(year, month, day)` is a **Gregorian civil date** — the day whose sunrise anchors
this pañcāṅga (traditionally, a pañcāṅga "day" runs sunrise-to-sunrise, not
midnight-to-midnight).

There's also a Julian-day-number entry point, useful when you already have a JD (e.g.
from ephemeris code) rather than a calendar date:

```python
from jyotisha.panchaanga.temporal import time as jtime

panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=city, julian_day=jtime.utc_gregorian_to_jd(Date(2018, 12, 31)))
```

## Reading the result

```python
print(panchaanga.julian_day_start)  # 2460324.2708333335 — JD of local midnight
print(panchaanga.jd_sunrise)        # 2460324.547738522
print(panchaanga.jd_sunset)         # 2460325.0190897435
print(panchaanga.jd_next_sunrise)   # 2460325.547849646
```

Julian day numbers are UTC-based floats; to get a human string back:

```python
from jyotisha.panchaanga.temporal import time as jtime
print(jtime.jd_to_utc_gregorian(panchaanga.jd_sunrise))  # 2024-01-15
```

### The five aṅgas (tithi, nakṣatra, yoga, karaṇa, + rāśi)

The cleanest way to read these off is `sunrise_day_angas.get_anga_data_md(...)`, which
returns a ready-to-display Markdown string — it also encodes *when* an aṅga changes
during the day (the number after `►` is the end time in hours-from-midnight,
`24:35!` meaning "one day + 35 minutes past midnight", i.e. it doesn't end until the next
day):

```python
from jyotisha.panchaanga.temporal.zodiac import AngaType
from indic_transliteration import sanscript

for anga_type in [AngaType.TITHI, AngaType.NAKSHATRA, AngaType.YOGA, AngaType.KARANA, AngaType.RASHI]:
    print(panchaanga.sunrise_day_angas.get_anga_data_md(
        anga_type=anga_type, script=sanscript.DEVANAGARI, reference_jd=panchaanga.julian_day_start))
```

Output for Chennai, 2024-01-15:

```
**तिथिः** — शुक्ल-पञ्चमी►26:17!; शुक्ल-षष्ठी►
**नक्षत्रम्** — शतभिषक्►08:05; पूर्वप्रोष्ठपदा►30:08!; उत्तरप्रोष्ठपदा►
**योगः** — वरीयान्►23:07; परिघः►
**करणम्** — बवम्►15:35; बालवम्►26:17!; कौलवम्►
**राशिः** — कुम्भः►24:35!; मीनः►
```

Read as: at sunrise the tithi is śukla-pañcamī, which ends at hour 26:17 (i.e. 02:17 the
*next* calendar day), after which it's śukla-ṣaṣṭhī for the rest of the visible window.
Pass `script=sanscript.IAST` (or another scheme from `indic_transliteration`) for
non-Devanagari output.

### The lunar month

```python
print(panchaanga.lunar_date.month.index)  # 10
```

Month index is a plain integer 1-12 — except during an adhika (intercalary) month, where
it becomes `month_number + 0.5` (see [03](03-computation-systems.md) and
[04](04-annual-panchaanga.md)).

### Festivals — why this comes back empty

```python
print(panchaanga.festival_id_to_instance)  # {}
```

A lone `DailyPanchaanga` **never has festivals attached**, even though the attribute
exists. Festival applicability rules (`puurvaviddha`/`paraviddha`/`vyaapti` — "does this
tithi need to touch a particular time-of-day, and if the boundary falls on two candidate
days, which one wins?") need neighboring days' data to resolve. Festivals only get
computed and attached when you build a full multi-day `Panchaanga` via
`annual.get_panchaanga_for_civil_year` (or similar) — see
[04-annual-panchaanga.md](04-annual-panchaanga.md). This is easy to trip over: printing
`festival_id_to_instance` on a single day and seeing `{}` does *not* mean "no festivals
on this day" — it means "this API can't tell you that."
