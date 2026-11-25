# Hand-off prompt: Smṛti-Kaustubha shlokas for adyatithi (Jyeṣṭha → Phālguna)

Paste everything below the line into a new Claude Code session that has the repositories
`jyotisham/adyatithi`, `jyotisham/jyotisha` and `stotrasamhita/smriti-kaustubham` attached.

---

## Task

Add verses (shlokas) from the **Smṛti-kaustubha** of Anantadeva (Nirṇaya Sāgara Press, 2nd ed., 1931) to
**existing** festival entries in `jyotisham/adyatithi`, one lunar month at a time, starting with **Jyeṣṭha**.
Chaitra and Vaiśākha are already done (adyatithi PRs #39, #40, #41). Work month by month in this order:

| Month | Printed pages | Folder in `stotrasamhita/smriti-kaustubham/content/samvatsara/` | Plan section |
|---|---|---|---|
| Jyeṣṭha | 117–137 | `jyestha-krtyam` | §5.3 |
| Āṣāḍha | 137–148 | `ashadha-krtyam` | §5.4 |
| Śrāvaṇa | 148–200 | `shravana-krtyam` | §5.5 |
| Bhādrapada | 201–287 | `bhadrapada-krtyam` | §5.6 |
| Āśvina | 287–357 | `ashvina-krtyam` | §5.7 |
| Kārtika | 358–427 | `kartika-krtyam` | §5.8 |
| Mārgaśīrṣa | 427–432 | `margashirsha-krtyam` | §5.9 |
| Pauṣa | 432–439 | `pausha-krtyam` | §5.10 |
| Māgha | 439–513 | `magha-krtyam` | §5.11 |
| Phālguna | 513–519 | `phalguna-krtyam` | §5.12 |
| Adhika-māsa, saṅkrānti etc. | 520–580 | `adhimasa`, `sankranti`, … | §5.13–5.14, §6.6 |

Large months (Śrāvaṇa, Bhādrapada, Āśvina, Kārtika, Māgha) may be split into two PRs.

## Inputs

1. **The plan:** `jyotisham/jyotisha`, branch `claude/cloud-session-question-hxioje`,
   file `plans/smriti_kaustubha_festival_upgrade.md` (§5 per month lists the candidate items, entry ids,
   key verses and pages) and `plans/smriti_kaustubha_notes.md` (fuller working notes). Treat these as a guide
   to *what to look for*, not as the source of verse text.
2. **The verse text:** always take it from the cleaned, tagged text in
   `stotrasamhita/smriti-kaustubham/content/samvatsara/<month>/*.md`, **not** from the raw OCR in
   `source/ocr/`. In those files:
   - `{{< pg N >}}` = printed page break (use it for page numbers in references);
   - `{{< q src="…" >}}…{{< /q >}}` = a quotation and its source (use the source for the attribution line);
   - `{{< corr ocr="…" >}}X{{< /corr >}}` = an OCR fix already made, keep X;
   - `{{< fn >}}…{{< /fn >}}` = 1931 footnote (variant reading), drop it from the shloka;
   - `[?]` = doubtful reading. **Keep `[?]` in the drafted text**; the reviewer decides whether to remove it.
   `docs/proofreading/<month>.md` lists every correction and doubtful reading by page if you need detail.
3. **The target:** `jyotisham/adyatithi` TOML files. Find an entry with
   `grep -rlF 'id = "<id>"' --include=*.toml .`. Tithi entries live under `…/lunar_month/tithi/MM/TT/`
   (month 01 = Chaitra; tithi 16–30 = kṛṣṇa pakṣa, amānta).

## Scope rules (decided by the owner — do not change)

- **Only add `shlokas` text and Smriti Kaustubham references to entries that already exist.**
- **No new festival files.** The plan's "NEW" items are out of scope for now; list them in the PR as "left out".
- **No timing changes** (`kaala`, `priority`, month/tithi numbers). Different traditions (e.g. Smṛti-muktāphala)
  decide these differently; the plan's §4 FIX list is deferred. If an added verse disagrees with an entry's
  current timing, add the verse anyway and say so in the review note and the PR body.
- Don't duplicate: before adding, check the entry's existing `shlokas`. Compare normalised text (drop spaces,
  daṇḍas, digits, avagraha; treat a class nasal before a consonant as anusvāra). Add only verses not already
  present. If an entry already has exactly SK's verse, add only the page reference.
- Skip ekādaśī entries, long prayoga/pūjā procedures, homa/kuṇḍa material, and udyāpana details.

## Formatting conventions (match PRs #40 and #41)

- Append to the existing `shlokas = """…"""` block after a blank line, or create the field (placed just above
  `jsonClass = "HinduCalendarEvent"`) if absent. Never edit or reorder existing verses.
- Each source gets a header line ending in `---`, e.g. `वाराहे---`, `मदनरत्ने स्कान्दे---`, `अर्घ्य-मन्त्रः---`.
  Set verses as half-verse lines ending `।` and `॥`. A short gloss may go in parentheses on its own line.
- End every added block with the line `---स्मृतिकौस्तुभे`.
- References: the spelling is exactly `Smriti Kaustubham p.NNN` or `p.NNN-NNN`. Append it to
  `references_primary` if that list exists, else to `references_secondary` (create one if neither exists).
  If the entry already cites Smriti Kaustubham, widen that reference instead of adding a second one.
- After editing, every changed file must parse: `python3 -c "import tomllib; tomllib.load(open(f,'rb'))"`.

## Workflow per month (the owner approves every edit before anything is pushed)

1. Read the plan's section for the month and the month's `content/` files.
2. List the adyatithi entries for that month (and any entries the plan names), and draft the additions under
   the rules above. Keep a JSON list of items: `{id, file, existing_shlokas, proposed_shlokas, ref, refkey, note}`.
   Notes should flag overlaps, `[?]` readings, and timing disagreements.
3. **Build the review page from the committed template** — don't design a new one. In `jyotisham/jyotisha`
   (same branch), `plans/sk_review_page/` has `template.html` (the exact page used for Vaiśākha),
   `build_page.py` (its docstring gives the item fields; `example_items.json` shows two real items) and
   `apply_decisions.py`. Write your items to a JSON file, then run
   `python3 plans/sk_review_page/build_page.py items.json "Jyeṣṭha" "117–137" decisions-jyestha review.html`
   and publish `review.html` as an Artifact with `capabilities: {"db": {}}` (one artifact for all months is fine:
   republish the same file path each month with a new collection name). Read the decisions back with the
   `ArtifactData` tool (`action: "list"`, `out_dir` set). Give the owner the link and a short summary table in
   chat. Do not push anything yet.
4. When the owner says they are done, save the decisions with `ArtifactData` `list` + `out_dir`, then run
   `python3 plans/sk_review_page/apply_decisions.py items.json <out_dir> /path/to/adyatithi` on a fresh branch
   (step 5). It applies only approved items, uses the owner's edited text, prints what they changed, and checks
   every file still parses. Tell the owner what they edited.
5. In `jyotisham/adyatithi`: branch `claude/smriti-kaustubha-<month>-shlokas` from the latest `master`
   (apply here, per step 4), commit and push. Commit message: a summary line, a short bullet list of entries,
   "Timing is unchanged. Reviewed and approved entry by entry.", and the attribution lines your session asks for.
6. Open a PR titled `Add <Month> shlokas from Smriti Kaustubham`, with a table of entry / added / pages and
   notes for `[?]` readings and timing disagreements. No PR template exists in the repo.
7. Merge only when the owner says so. Before merging, check that the `generate (3.12)` CI check on the PR head
   has passed (`gh api repos/jyotisham/adyatithi/commits/<sha>/check-runs`). Use a merge commit
   (`gh api -X PUT repos/jyotisham/adyatithi/pulls/<n>/merge -f merge_method=merge -f sha=<sha>`).
   Note: `gh pr …` commands use GraphQL and may be blocked; use `gh api` REST calls.
8. Move to the next month.

## Examples to copy

- Merged PRs: jyotisham/adyatithi #40 (Chaitra) and #41 (Vaiśākha) — look at their diffs for the exact shape
  of the additions and references.
- Known quirks found so far: `[?]` marks in the source are kept unless the owner removes them; the nṛsiṃha arghya
  mantra has "हिरण्याक्ष [?]"; the śukla-yugādi pūrvāhṇa verse disagrees with current yugādi timing.

## Don't

- Don't push or open a PR before the owner has approved the batch on the review page.
- Don't change timing, add new festivals, or edit `stotrasamhita/smriti-kaustubham`.
- Don't take verse text from the raw OCR when the cleaned `content/` text exists.
