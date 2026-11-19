# Writers: turning a `Panchaanga` into Markdown / ICS / TeX

All three writers take an already-computed `Panchaanga` (the annual/periodical object
from [04-annual-panchaanga.md](04-annual-panchaanga.md), not a bare `DailyPanchaanga`) —
so festival data is available. The examples below load the repo's precomputed
`Chennai-2019.json` fixture instead of recomputing, to keep them fast to try:

```python
import logging
logging.disable(logging.CRITICAL)
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga

panchaanga = Panchaanga.read_from_file(filename="jyotisha_tests/spatio_temporal/data/Chennai-2019.json")
```

## Markdown

```python
from jyotisha.panchaanga.writer import md

md_content = md.make_md(panchaanga=panchaanga)
print(len(md_content))  # 2612359 characters for a full year, devanagari script by default
```

The output starts with a computation-parameters section (a TOML dump of the
`ComputationSystem` used, plus links to every festival repo consulted), then one section
per day:

```
### Computation parameters
...
## 2019-01
### 2019-01-01

#### मार्गशीर्षः-09-26  ,तुला-स्वाती🌛🌌  ,  धनुः-पूर्वाषाढा-09-17🌞🌌  ,  तपः-11-11🌞🪐  , मङ्गलः
- Indian civil date: 1940-10-11, Islamic: 1440-04-23 Rabīʿ ath-Thānī/ al-ʾĀkhir, ...
- संवत्सरः - विलम्बः
```

To write it to a file with proper front-matter, this project uses its sibling
`doc-curation` package rather than plain file I/O (as shown in
`jyotisha_tests/spatio_temporal/writer/test_md.py`):

```python
from doc_curation.md.file import MdFile

md_file = MdFile(file_path="/some/path.md")
md_file.dump_to_file(metadata={"title": "2019"}, content=md_content, dry_run=False)
```

## ICS (calendar file, importable into Google/Apple/Outlook calendars)

```python
from jyotisha.panchaanga.writer.ics import compute_calendar, write_to_file
from indic_transliteration import sanscript

ics_calendar = compute_calendar(panchaanga, scripts=[sanscript.ISO], set_sequence=False)
write_to_file(ics_calendar, "/some/path.ics")
```

`scripts` controls the transliteration scheme used for event summaries/descriptions —
`sanscript.ISO` (IAST-like) above, or e.g. `sanscript.DEVANAGARI`. Each day becomes one
all-day-spanning `VEVENT` (from that day's sunrise to the next), e.g.:

```
BEGIN:VEVENT
SUMMARY:Mārgaśīrṣaḥ-09-26  \,Tulā-Svātī🌛🌌  \,  Dhanuḥ-P
 ūrvāṣāḍhā-09-17🌞🌌  \,  Tapaḥ-11-11🌞🪐  \, Maṅgala
 ḥ
DTSTART;TZID=Asia/Calcutta:20190101T063447
DTEND;TZID=Asia/Calcutta:20190102T063513
DTSTAMP:20260913T215020Z
UID:20190101_day_summary
DESCRIPTION:- Indian civil date: 1940-10-11\, Islamic: 1440-04-23 ...
END:VEVENT
```

### Pitfall: `DTSTAMP` is wall-clock time by default — breaks byte-for-byte comparisons

`compute_calendar` stamps every event's `DTSTAMP` with `datetime.now()` at generation
time unless you pass `dtstamp=` explicitly. That's correct RFC 5545 behavior for real
calendar output, but it means regenerating the same `.ics` twice produces a diff on
every single event. If you're comparing generated output against a golden fixture (as
this repo's own `jyotisha_tests/spatio_temporal/writer/test_ics.py` does), pass a fixed
`dtstamp`:

```python
from datetime import datetime, timezone
ics_calendar = compute_calendar(panchaanga, scripts=[sanscript.ISO], set_sequence=False,
                                 dtstamp=datetime(2020, 1, 1, tzinfo=timezone.utc))
```

## TeX (for print-ready PDF calendars)

```python
from jyotisha.panchaanga.writer.tex.daily_tex_writer import emit
from indic_transliteration import sanscript

panchaanga.update_festival_details()  # required — see pitfall below
with open("/some/path.tex", "w") as f:
    emit(panchaanga, output_stream=f, languages=["sa", "ta"],
         scripts=[sanscript.DEVANAGARI, sanscript.TAMIL])
```

`languages`/`scripts` are parallel lists — each language gets rendered in the
corresponding script (here: Sanskrit in Devanagari, Tamil in Tamil script), both shown
side by side per day. The output is a self-contained XeLaTeX document (needs `xelatex`,
not `pdflatex`, per its first line `% !Tex program = xelatex`) with a small-card page
size (`135mm × 180mm`) intended for daily desk calendars.

### Pitfall: `emit()` needs `update_festival_details()` called first

Unlike the Markdown and ICS writers, the TeX daily writer expects
`panchaanga.update_festival_details()` to have been called beforehand (see
`jyotisha_tests/spatio_temporal/writer/test_annual_daily_tex.py`). A freshly
`annual.get_panchaanga_for_civil_year(...)`-computed `Panchaanga` already has this done
as part of computation; a `Panchaanga` you loaded via `read_from_file` from an older
cache may not, if festival rule data has since changed — call it explicitly to be safe.
