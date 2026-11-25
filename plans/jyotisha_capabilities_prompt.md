# Hand-off prompt: new festival-rule capabilities in jyotisha

Paste everything below the line into a new Claude Code session with `jyotisham/jyotisha` and
`jyotisham/adyatithi` attached (add `stotrasamhita/smriti-kaustubham` to read the source text).

---

## Task

Add the festival-timing rules that the jyotisha engine cannot yet express, so that festivals whose dates
depend on them *can* be computed correctly. Work one capability at a time, one PR per capability, starting
with **C1 (bhadrā)**. Design first, then build, then test.

**Key constraint: no computed date may change unless an adyatithi entry opts in.** Every capability is a new,
optional field or rule on the timing schema; existing entries and their output must stay byte-identical.
The owner has deferred timing changes to adyatithi entries (traditions such as Smṛti-muktāphala and
Smṛti-kaustubha disagree), so this work only makes the rules *available*. Switching a real festival over to a
new rule is a separate decision the owner makes later; don't do it in these PRs.

## Background

- The plan that identified these gaps: `jyotisham/jyotisha`, branch `claude/cloud-session-question-hxioje`,
  `plans/smriti_kaustubha_festival_upgrade.md` §3.2 (capabilities C1–C10) and §4 (the festivals that would use
  them). `plans/smriti_kaustubha_notes.md` has the source verses. (These files may since have moved to a
  branch on `jyotisham/adyatithi`; look there if not found.)
- The source text, cleaned and with printed page numbers, is in
  `stotrasamhita/smriti-kaustubham/content/samvatsara/`; the rule verses for each capability are cited by page
  in the plan.
- Code to read first:
  - `jyotisha/panchaanga/temporal/festival/rules/__init__.py` — `HinduCalendarEvent` / `HinduCalendarEventTiming`
    (already supports `intersection_groups` over tithi/nakshatra/yoga/karana/vaara/solar_nakshatra/
    nakshatra_pada, `vaara`, `angas`, `adhika_maasa_handling`, `anchor_festival_id`/offset);
  - `jyotisha/panchaanga/temporal/festival/priority_decision.py` — `puurvaviddha` / `paraviddha` / `vyaapti`
    decisions and the kaala offsets;
  - `jyotisha/panchaanga/temporal/festival/applier/` — `tithi_festival.py`, `solar.py` (padmaka, ardhodaya/
    mahodaya), `vaara.py`, `upakarma.py`, `ecliptic.py`;
  - kaala names in `jyotisha/panchaanga/temporal/names/__init__.py`;
  - `docs-guide/06-festivals.md`.
- Tests: `jyotisha_tests/` (pytest; `spatio_temporal/test_annual.py` compares generated annual panchāṅgas with
  stored expected output) and `jyotisha_manual_tests/temporal/festival/applier/` (examples of applier tests).
  Run the existing suite before and after each change; the stored expected outputs must not change.

## The capabilities, in suggested order

| # | Capability | Why first / later | Festivals that would use it |
|---|---|---|---|
| C1 | **Bhadrā (viṣṭi karaṇa) segmentation**: compute bhadrā intervals; split into mukha 5 ghaṭī, kaṇṭha 1, hṛdaya 11, nābhi 4, kaṭi 6, puccha 3 (Nārada, SK p.564–565); a timing option "kaala must avoid bhadrā", with the SK fall-back chain (bhadrā-free pradoṣa → after bhadrā ends before dawn → bhadrā-puccha → in bhadrā). | Self-contained; two major festivals need it | Holikā (SK p.516–518), Rakṣābandhana (p.167) |
| C9 | **Solar month as a condition** combined with a lunar tithi (sun in a rāśi on the day). First check whether `intersection_groups` can already do this; if so, document it and add a test instead of code. | May already exist | mahā-ṣaṣṭhī (vṛścika + kārtika ś6 + bhauma), ulkā-dāna (sun in tulā), Dūrvāṣṭamī (siṃha only) |
| C2 | **Graha in nakṣatra**: Jupiter / Moon / Sun in a given nakṣatra (and the sun in the second half of one) as a condition. | Needs graha longitudes per day | mahā-jyeṣṭhī, mahā-kārtikī, padmaka, kapilā-ṣaṣṭhī, gajacchāyā |
| C3 | **Nakṣatra overrides kaala-vyāpti**: if a named nakṣatra is joined with the tithi on one of the two days, that day wins regardless of the usual vyāpti rule. | Core of Janmāṣṭamī | Janmāṣṭamī / Jayantī (p.181–187), aparājitā with śravaṇa (p.352), jyeṣṭhā-gaurī |
| C4 | **Nakṣatra exclusion**: a day is rejected if a named nakṣatra is present (with a fall-back). | Small once C3 exists | Dūrvāṣṭamī ("ज्येष्ठामूलं विवर्जयेत्", p.229–230) |
| C6 | **Next-day duration rules**: decide by how long the tithi (or the next tithi) lasts on the second day (≥ N yāma / muhūrta). | Generalises several ad-hoc rules | Govardhana (p.374), Holikā pratipat fall-back (p.518), trispṛśā śivarātri (p.483) |
| C5 | **Month fall-back**: if a condition isn't met in month M, look in month M+1. | Depends on C3 | Jayantī (Śrāvaṇa → Bhādrapada, p.194–195) |
| C7 | **Nakṣatra-upavāsa rule**: choose the day whose sunset (else niśītha) has the nakṣatra. | Check whether `kaala` on a nakṣatra already does this | nakṣatra vratas (p.562) |
| C10 | **Adhika-māsa audit**: compare `adhika_maasa_handling` of festivals against SK p.525–529 (nija-only, adhika-only, both). Produce a report, not code. | Report for the owner | yugādi/manvādi śrāddha, first upākarma, cāturmāsya |
| C8 | Two grahas in a rāśi | Leave for last or skip | Vaiśākha ś12 "vyatīpāta" (p.114) |

## Workflow per capability

1. Read the relevant code and the SK verses for that capability. Write a short design note in the PR description:
   the new schema field(s) and their TOML spelling, the algorithm, the default (off), and edge cases
   (high latitudes, a tithi spanning three days, kṣaya/vṛddhi tithis).
2. Before writing code, tell the owner the proposed TOML spelling in chat (one example entry) and get a yes;
   the schema is shared with adyatithi and hard to change later.
3. Implement with unit tests that pin known dates. For each test date, say where the expected answer comes
   from (a published pañcāṅga, or a worked example from the SK text), not from the new code's own output.
4. Show that existing output is unchanged: the full test suite passes and the stored annual outputs don't move.
5. Add an *example* adyatithi TOML in the PR description (not committed to adyatithi) showing how a festival
   would opt in, and the dates it would produce for 3 years at one or two locations, next to the current dates.
6. Open the PR on `jyotisham/jyotisha`; merge only when the owner says so and CI is green
   (`gh pr …` uses GraphQL and may be blocked; use `gh api` REST calls).

## Don't

- Don't change the timing of any existing adyatithi entry, and don't open PRs on adyatithi for this work.
- Don't change default behaviour of `priority`, `kaala` or existing appliers.
- Don't take test expectations from the code under test.
