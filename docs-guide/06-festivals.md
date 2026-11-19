# Festival rules: data format, querying, and customizing

## Where the data lives

Festival/observance definitions are **not** Python code — they're ~1,700 TOML files (one
per festival) vendored as a git submodule
([`adyatithi`](https://github.com/jyotisham/adyatithi)) at
`jyotisha/panchaanga/temporal/festival/data/`. See
`jyotisha/panchaanga/temporal/festival/data/README.md` for the authoritative spec; this
page is the practical walkthrough.

```bash
find jyotisha/panchaanga/temporal/festival/data -name "*.toml" | wc -l   # 1694
```

If that directory is empty for you, you haven't initialized the submodule — see
[01-installation.md](01-installation.md).

## Repositories

Festivals are grouped into **repositories** — topical/community groupings like `tamil`,
`temples/Tamil`, `gRhya/general`, `mahApuruSha/kAnchI-maTha`, `devatA/gaNapati` — so
consumers can opt in/out of festival categories they don't care about (a
Kāñcī-maṭha-affiliated user may not want every Tamil nāyanmār's guru-pūjā, say). The
list of repositories is itself data: `jyotisha/panchaanga/temporal/festival/data/repos.toml`,
loaded once at import time into `jyotisha.panchaanga.temporal.festival.rules.rule_repos`
(65 entries, as of this writing):

```python
from jyotisha.panchaanga.temporal.festival import rules
print(len(rules.rule_repos))          # 65
print(rules.rule_repos[0].name, rules.rule_repos[0].base_url)
# devatA/gaNapati https://github.com/jyotisham/adyatithi/blob/master/devatA/gaNapati
```

A `ComputationSystem`'s `festival_options.repos` (see
[03-computation-systems.md](03-computation-systems.md)) defaults to this list minus one
repo excluded by default (a `viSuvAdi`-named repo, filtered out because the default
`tropical_month_start="mAdhava_at_equinox"` setting excludes it — see
`FestivalOptions.__init__`), i.e. 64 repos, and can be narrowed further with
`fest_repos` / `fest_repos_excluded_patterns`.

## One festival = one TOML file, path-encoded by timing

Within a repository, a festival's file *path* encodes when it happens, so the data can
be looked up without parsing every file. For a festival independently timed by a
lunar-month + aṅga combination:

```
[repo]/[month_type]/[anga_type]/[month_number]/[anga_number]/[festival_id].toml
```

For example, `zrIvinAyaka-caturthI.toml` (Gaṇeśa Caturthī) lives at
`devatA/gaNapati/lunar_month/tithi/06/04/zrIvinAyaka-caturthI.toml` — lunar month 6
(Bhādrapada), tithi 4 (caturthī):

```toml
default_to_none = true
id = "zrIvinAyaka-caturthI"
tags = [ "CommonFestivals",]
references_primary = [ "Bhavishya Puranam",]
jsonClass = "HinduCalendarEvent"
shlokas = """
... (verses justifying the timing rule) ...
"""

[timing]
default_to_none = true
month_type = "lunar_month"
priority = "puurvaviddha"
month_number = 6
anga_type = "tithi"
anga_number = 4
kaala = "मध्याह्नः"
jsonClass = "HinduCalendarEventTiming"

[names]
sa = [ "श्रीविनायक-चतुर्थी",]
```

Key fields:
- **`timing.kaala`** — the time-of-day interval (here `मध्याह्नः`, madhyāhna/midday) that
  the aṅga must intersect for the day to qualify. Common values: prāktana-aruṇodaya
  (dawn *preceding* the day), sūryodaya (sunrise), sūryāstamaya (sunset), pūrvāhṇa,
  aparāhṇa.
- **`timing.priority`** — when the aṅga+kaala intersection spans two consecutive days,
  which wins: `puurvaviddha` (earlier day), `paraviddha` (later day), or `vyaapti`
  (whichever day has the larger overlap). See `priority_decision.py`.
- **`names`** — per-script/language display names, keyed by language code (`sa` =
  Sanskrit here).
- **`shlokas`** / `references_primary` / `references_secondary` — textual justification;
  `shlokas` supports inline `+++(comment)+++` markup per the data README.

Other path shapes exist for other cases (see the data README for the full list):
- Relatively-timed festivals (N days after another festival):
  `[repo]/[anchor_festival_id]/offset__[day]/[festival_id].toml`.
- Festivals without a simple timing rule (described in prose, timing handled specially
  in code): `[repo]/description_only/[festival_id].toml` — e.g.
  `tamil/description_only/viSukkan2i.toml`.

You don't need to hand-craft these paths: `jyotisha/panchaanga/temporal/festival/rules/migrator.py`
recomputes the canonical path for a rule and moves the file there for you.

## Querying rules programmatically

`RulesCollection` loads and indexes every rule from a tuple of repos into both a flat
`name_to_rule` dict (by festival id) and a nested `tree` keyed by the same path
components used on disk:

```python
from jyotisha.panchaanga.temporal.festival import rules

rule_set = rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)

# Flat lookup by id:
vinayaka_rule = rule_set.name_to_rule["zrIvinAyaka-caturthI"]
print(vinayaka_rule.timing.month_number, vinayaka_rule.timing.anga_number)  # 6 4

# Tree lookup by (month_type, anga_type, month, anga) — note zero-padded string keys:
from sanskrit_data import collection_helper
pura = rule_set.tree[rules.RulesRepo.LUNAR_MONTH_DIR][rules.RulesRepo.TITHI_DIR]["00"]["15"]
print([k for k in pura.keys() if k != collection_helper.LEAVES_KEY])
# ['pUrNimA~pUjA', 'pancha-parva-2', 'pUrNimA~vratam', 'adhika-mAsa-pUrNimA', ...]
# -- festival ids that fall on (any) month, tithi 15 (full moon). Each tree node also
# carries a collection_helper.LEAVES_KEY ("_LEAVES") entry holding the actual rule
# objects at that node -- filter it out (as above) when you just want the id list.

# Resolve a rule's canonical source URL (in the adyatithi repo on GitHub):
print(vinayaka_rule.get_url())
```

(`RulesRepo.LUNAR_MONTH_DIR`, `.TITHI_DIR`, `.NAKSHATRA_DIR`, `.YOGA_DIR`,
`.GREGORIAN_MONTH_DIR`, `.DAY_DIR`, `.SIDEREAL_SOLAR_MONTH_DIR` etc. are the string
constants used as tree/path keys — use these instead of hardcoding the strings, in case
they change.)

### Pitfall: month number `"00"` means "any month"

Festivals tied to a tithi/nakṣatra/yoga regardless of which lunar month it occurs in
(e.g. every full moon, every ekādaśī) are filed under month **`00`** in the tree, not
omitted or under a special sentinel — as seen above with `pUrNimA~vratam` under
`["lunar_month"]["tithi"]["00"]["15"]`. If you're walking the tree assuming month keys
are always `"01"`-`"12"`, you'll miss (or crash on) these.

## Reading which festivals actually landed on a computed date

The rule data alone doesn't tell you *when* (in a given year, for a given place) a
festival actually falls — the "puurvaviddha vs. paraviddha" tie-breaking, adhika-month
handling, and kaala-intersection logic are applied per-year by the festival appliers
in `jyotisha/panchaanga/temporal/festival/applier/`, driven by a `ComputationSystem`'s
`festival_options`, during `annual.get_panchaanga_for_civil_year(...)` (or similar).
See [04-annual-panchaanga.md](04-annual-panchaanga.md) for reading the results off a
computed `Panchaanga` (`festival_id_to_days`, `DailyPanchaanga.festival_id_to_instance`).

## Adding or customizing a festival

1. Pick (or create) a repository under `jyotisha/panchaanga/temporal/festival/data/`
   matching the festival's category, and add it to `repos.toml` if it's new.
2. Write a new `.toml` file with at minimum `id`, `jsonClass = "HinduCalendarEvent"`,
   a `[timing]` block (`jsonClass = "HinduCalendarEventTiming"`, plus `month_type`,
   `anga_type`, `month_number`, `anga_number`, `kaala`, `priority`), and a `[names]`
   block — using `zrIvinAyaka-caturthI.toml` above as a template. Placing it at a
   throwaway path is fine; running the migrator script moves it to the canonical path.
3. Give the file's `id` field the same value as its filename (enforced by tooling
   eventually, per the data README) and avoid `/` or spaces in `id`.
4. Since this data lives in the separate `adyatithi` repository (submodule), you'll be
   contributing there, not in `jyotisha` itself — commit inside
   `jyotisha/panchaanga/temporal/festival/data/`, which git will treat as a submodule
   change.
5. Verify by computing a `Panchaanga` for a year/place you know the festival's real-world
   date for, and checking it shows up in `festival_id_to_days` on the expected date (as
   done for `zrIvinAyaka-caturthI` in [04-annual-panchaanga.md](04-annual-panchaanga.md)).
