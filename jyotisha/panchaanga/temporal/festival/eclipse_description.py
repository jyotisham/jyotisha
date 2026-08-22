"""Dynamic description generation for eclipse ("grahaNa") festivals.

Eclipse festival ids are combinatorial (node x grastOdaya/grastAstamana/plain
x cUDAmaNi), and every individual occurrence differs in magnitude and timing.
Rather than maintaining a static TOML description file per combination (which
also forces every eclipse of a given "type" to share one canned description),
this module computes the astronomical circumstances of each occurrence
(computed by ecliptic.py at the time the festival instance is created) into a
plain dict of substitution fields. The actual wording is a Python
str.format()-style template living in a TOML rule (sUrya-grahaNa-varNanam /
candra-grahaNa-varNanam -- see template_description.render_template), editable
without touching code; only the short, purely-factual `blurb` is still
composed directly here, since (like ekadashi/pushkara's blurb) it has no
get_timing_summary()-equivalent and isn't the kind of text that benefits from
editorial rewording.

Food-restriction (bhojana-niyama) timing and the graha-shanti nakshatra/rashi
rules below follow this panchaanga's own "General notes for all grahanas"
instructions.

Unlike PushkaraFestivalInstance/EkadashiFestivalInstance, eclipses are NOT
given their own FestivalInstance subclass. Those subclasses exist to carry
family-specific *naming* logic (deriving a fest_id from role/rashi/paksha
etc.) alongside the description. ecliptic.py already builds each eclipse's
fest_id directly from swisseph data with no such derivation to centralize,
and eclipses need no behavioral difference from plain FestivalInstance --
tex_code/md_code and both description pipelines run completely unmodified.
A subclass here would only relocate this module's calls into __init__ with
a large raw-astronomy parameter list, coupling festival/__init__.py to
eclipse-specific data for no functional gain. The free-function-module
pattern (this file, invoked directly from ecliptic.py at FestivalInstance
construction time) is the right shape whenever a family has no special
behavior, just a special description.
"""
import swisseph as swe
from indic_transliteration import sanscript

from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import AngaType

NODE_NAMES = {
  'rAhumukhagrast': dict(en='Rahu node (mukha/ascending)'),
  'rAhupucchagrast': dict(en='Rahu node (puccha/descending)'),
}

# Devanagari roots for the human-readable `names` dict (get_human_names()).
# Both nodes are attributed to Rahu (mukha = ascending, puccha = descending)
# rather than invoking "Ketu" as a separately-named node -- Rahu/Ketu as two
# distinct entities is an older convention; the mukha/puccha framing (already
# used by the fest_id itself, e.g. 'rAhupucchagrasta') is more precise.
# Without this, display falls back to auto-transliterating the raw fest_id.
_NODE_SA_ROOT = {
  'rAhumukhagrast': 'राहुमुखग्रस्त',
  'rAhupucchagrast': 'राहुपुच्छग्रस्त',
}
_SUFF_SA = {
  'a': '',
  'Odaya': 'ोदय',
  'Astamana': 'ास्तमन',
}


def sanskrit_name(luminary_sa, grasta, suff, is_cudamani):
  """:param luminary_sa: 'सूर्य' or 'चन्द्र'"""
  name = "%s-ग्रहणम्~(%s%s)" % (luminary_sa, _NODE_SA_ROOT[grasta], _SUFF_SA[suff])
  if is_cudamani:
    name = "★चूडामणि-" + name
  return {"sa": [name]}

# Food restriction begins at the start of the yaama that is 4 yaamas (solar)
# or 3 yaamas (lunar) before the yaama in which first contact falls -- not a
# flat 12h/9h offset from the contact instant. num_yaamas_before is passed
# the aligned yaama list computed in ecliptic.py; hours-based figures below
# are only the fallback used if that alignment isn't available.
SOLAR_NIYAMA_YAAMAS_BEFORE = 4
LUNAR_NIYAMA_YAAMAS_BEFORE = 3
SOLAR_NIYAMA_HOURS_BEFORE_FALLBACK = 12
LUNAR_NIYAMA_HOURS_BEFORE_FALLBACK = 9


def yaama_aligned_start(yaama_intervals, jd, n_yaamas):
  """
  :param yaama_intervals: chronologically-ordered Intervals (jd_start/jd_end), each ~a yaama,
    spanning enough time to contain `jd` and at least `n_yaamas` before it
  :param jd: the instant to locate (e.g. first contact)
  :param n_yaamas: how many yaamas to step back
  :return: jd_start of the yaama `n_yaamas` before the one containing `jd`, or None if `jd`
    isn't covered or stepping back runs past the start of `yaama_intervals`
  """
  idx = None
  for i, y in enumerate(yaama_intervals):
    if y.jd_start is not None and y.jd_end is not None and y.jd_start <= jd < y.jd_end:
      idx = i
      break
  if idx is None or idx - n_yaamas < 0:
    return None
  return yaama_intervals[idx - n_yaamas].jd_start

# Nakshatra offsets (from the grahaNa nakshatra, 0-indexed) that receive
# ashubha phala: preceding, the grahaNa nakshatra itself, succeeding, the
# 10th (anujanma) and 19th (trijanma) counted inclusively from it.
SHANTI_NAKSHATRA_OFFSETS = [-1, 0, 1, 9, 18]

# Rashi phala, counted inclusively from the grahaNa rashi (1 = the grahaNa
# rashi itself).
RASHI_PHALA_POSITIONS = {
  'shubha': [3, 4, 8, 11],
  'ashubha': [5, 7, 9, 12],
  'more_ashubha': [1, 2, 6, 10],
}

REFERENCE_NOTE = (
  "- References\n"
  "  - Food-restriction timing and graha-shanti nakshatra/rashi lists follow this pancAnga's "
  "\"General notes for all grahanas\" instructions.\n"
)


def _solar_eclipse_type(retflag):
  if retflag & swe.ECL_ANNULAR_TOTAL:
    return 'annular-total (hybrid)'
  if retflag & swe.ECL_TOTAL:
    return 'total'
  if retflag & swe.ECL_ANNULAR:
    return 'annular'
  if retflag & swe.ECL_PARTIAL:
    return 'partial'
  return 'eclipse'


def _lunar_eclipse_type(retflag):
  if retflag & swe.ECL_TOTAL:
    return 'total'
  if retflag & swe.ECL_PARTIAL:
    return 'partial'
  if retflag & swe.ECL_PENUMBRAL:
    return 'penumbral'
  return 'eclipse'


def _suffix_clause(suff, rise_or_set_word):
  """A ready-made, already-punctuated sentence (or '' if `suff` is plain) -- a template
  {placeholder} can't itself express "include this sentence only if grastOdaya/grastAstamana",
  so the conditional lives here instead."""
  if suff == 'Odaya':
    return "The eclipse is already in progress at %s (grastodaya). " % rise_or_set_word[0]
  if suff == 'Astamana':
    return "The eclipse is still in progress at %s (grastAstamana). " % rise_or_set_word[1]
  return ''


def _shanti_fields(nakshatra_index, rashi_index):
  """Substitution fields for the graha-shanti nakshatra/rashi clause (see
  SHANTI_NAKSHATRA_OFFSETS/RASHI_PHALA_POSITIONS). Names are raw HK-Dravidian roman --
  backtick-wrapped in the template and transliterated to the final output script downstream
  (the same deferred-transliteration convention every other backtick-quoted term follows), not
  resolved to a specific script here."""
  nak_names_dict = AngaType.NAKSHATRA.names_dict[sanscript.roman.HK_DRAVIDIAN]
  nak_names = [nak_names_dict[((nakshatra_index - 1 + o) % 27) + 1] for o in SHANTI_NAKSHATRA_OFFSETS]
  rashi_names_dict = AngaType.RASHI.names_dict[sanscript.roman.HK_DRAVIDIAN]
  rashi_phala = {
    category: [rashi_names_dict[((rashi_index - 1 + (pos - 1)) % 12) + 1] for pos in positions]
    for category, positions in RASHI_PHALA_POSITIONS.items()
  }
  return dict(
    shanti_nakshatra='/'.join(nak_names[0:3]),
    anujanma_nakshatra=nak_names[3],
    trijanma_nakshatra=nak_names[4],
    rashi_more_ashubha=', '.join(rashi_phala['more_ashubha']),
    rashi_ashubha=', '.join(rashi_phala['ashubha']),
    rashi_shubha=', '.join(rashi_phala['shubha']),
  )


def solar_eclipse_fields(grasta, suff, is_cudamani, attr, retflag, jd_contact_start, jd_contact_end, nakshatra_index,
                          rashi_index, tz, niyama_start_jd=None, script=sanscript.ISO):
  """
  Substitution fields for the sUrya-grahaNa-varNanam TOML template, plus a ready-made `blurb`.

  :param grasta: 'rAhumukhagrast' or 'rAhupucchagrast'
  :param suff: 'a' (plain), 'Odaya' (grastodaya) or 'Astamana' (grastAstamana)
  :param attr: the 20-tuple returned by swe.sol_eclipse_when_loc as its 3rd element
  :param retflag: the int retflag returned by swe.sol_eclipse_when_loc
  :param jd_contact_start: first-contact JD (unclipped by sunrise/sunset)
  :param jd_contact_end: last-contact JD (unclipped by sunrise/sunset)
  :param nakshatra_index: 1-indexed nakshatra of the eclipse (Sun/Moon are conjunct)
  :param rashi_index: 1-indexed rashi of the eclipse
  :param tz: a Timezone instance, for rendering the food-restriction window
  :param niyama_start_jd: start of food restriction, yaama-aligned (see yaama_aligned_start);
    falls back to a flat SOLAR_NIYAMA_HOURS_BEFORE_FALLBACK offset from jd_contact_start if None
  :return: (blurb, fields)
  """
  node_en = NODE_NAMES[grasta]['en']
  ecl_type = _solar_eclipse_type(retflag)
  magnitude = attr[0]
  parimana_angula = magnitude * 12

  blurb = "%s solar eclipse (parimāṇa ≈%.1f of 12 aṅgulas), Sun at the %s. " % (
    ecl_type.capitalize(), parimana_angula, node_en)

  if niyama_start_jd is None:
    niyama_start_jd = jd_contact_start - SOLAR_NIYAMA_HOURS_BEFORE_FALLBACK / 24.0
  niyama_text = Interval(jd_start=niyama_start_jd, jd_end=jd_contact_end, name='bhojana-niyama').to_hour_text(tz=tz, script=script)

  fields = dict(
    suffix_clause=_suffix_clause(suff, ('sunrise', 'sunset')),
    magnitude_pct='%.0f' % (magnitude * 100),
    parimana_angula='%.1f' % parimana_angula,
    niyama_text=niyama_text,
    niyama_yaamas=SOLAR_NIYAMA_YAAMAS_BEFORE,
    cudamani_clause="Falling on a Sunday, this is an especially auspicious `cUDAmaNi` (crest-jewel) eclipse. " if is_cudamani else '',
  )
  fields.update(_shanti_fields(nakshatra_index, rashi_index))
  return blurb, fields


def lunar_eclipse_fields(grasta, suff, is_cudamani, attr, retflag, jd_contact_start, jd_contact_end, nakshatra_index,
                          rashi_index, tz, niyama_start_jd=None, script=sanscript.ISO):
  """
  Substitution fields for the candra-grahaNa-varNanam TOML template, plus a ready-made `blurb`.

  :param attr: the 20-tuple returned by swe.lun_eclipse_when_loc as its 3rd element
  :param retflag: the int retflag returned by swe.lun_eclipse_when_loc
  :param jd_contact_start: penumbral-begin JD (unclipped by moonrise/moonset)
  :param jd_contact_end: penumbral-end JD (unclipped by moonrise/moonset)
  :param nakshatra_index: 1-indexed nakshatra of the eclipsed Moon
  :param rashi_index: 1-indexed rashi of the eclipsed Moon
  :param niyama_start_jd: start of food restriction, yaama-aligned; falls back to a flat
    LUNAR_NIYAMA_HOURS_BEFORE_FALLBACK offset from jd_contact_start if None
  :return: (blurb, fields)
  """
  node_en = NODE_NAMES[grasta]['en']
  ecl_type = _lunar_eclipse_type(retflag)
  magnitude = attr[0]  # umbral magnitude; can exceed 1.0 for total eclipses
  parimana_angula = min(magnitude, 1.0) * 12

  blurb = "%s lunar eclipse (parimāṇa ≈%.1f of 12 aṅgulas), Moon at the %s. " % (
    ecl_type.capitalize(), parimana_angula, node_en)

  if niyama_start_jd is None:
    niyama_start_jd = jd_contact_start - LUNAR_NIYAMA_HOURS_BEFORE_FALLBACK / 24.0
  niyama_text = Interval(jd_start=niyama_start_jd, jd_end=jd_contact_end, name='bhojana-niyama').to_hour_text(tz=tz, script=script)

  fields = dict(
    suffix_clause=_suffix_clause(suff, ('moonrise', 'moonset')),
    magnitude='%.2f' % magnitude,
    parimana_angula='%.1f' % parimana_angula,
    niyama_text=niyama_text,
    niyama_yaamas=LUNAR_NIYAMA_YAAMAS_BEFORE,
    cudamani_clause="Falling on a Monday, this is an especially auspicious `cUDAmaNi` (crest-jewel) eclipse. " if is_cudamani else '',
  )
  fields.update(_shanti_fields(nakshatra_index, rashi_index))
  return blurb, fields
