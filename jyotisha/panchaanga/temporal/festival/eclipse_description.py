"""Dynamic description generation for eclipse ("grahaNa") festivals.

Eclipse festival ids are combinatorial (node x grastOdaya/grastAstamana/plain
x cUDAmaNi), and every individual occurrence differs in magnitude and timing.
Rather than maintaining a static TOML description file per combination (which
also forces every eclipse of a given "type" to share one canned description),
this module builds the description directly from the astronomical
circumstances of each occurrence, computed by ecliptic.py at the time the
festival instance is created.

Food-restriction (bhojana-niyama) timing and the graha-shanti nakshatra/rashi
rules below follow this panchaanga's own "General notes for all grahanas"
instructions.
"""
import swisseph as swe
from indic_transliteration import sanscript

from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import AngaType

NODE_NAMES = {
  'rAhumukhagrast': dict(en='Rahu node (ascending/mukha)'),
  'rAhupucchagrast': dict(en='Ketu node (descending/puccha)'),
}

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


def _suffix_note(suff, rise_or_set_word):
  if suff == 'Odaya':
    return "already in progress at %s (grastodaya)" % rise_or_set_word[0]
  if suff == 'Astamana':
    return "still in progress at %s (grastAstamana)" % rise_or_set_word[1]
  return None


def _shanti_nakshatra_names(nakshatra_index, script):
  names_dict = AngaType.NAKSHATRA.names_dict[script]
  names = [names_dict[((nakshatra_index - 1 + o) % 27) + 1] for o in SHANTI_NAKSHATRA_OFFSETS]
  return names  # [preceding, grahaNa, succeeding, anujanma (10th), trijanma (19th)]


def _rashi_phala_names(rashi_index, script):
  names_dict = AngaType.RASHI.names_dict[script]
  return {
    category: [names_dict[((rashi_index - 1 + (pos - 1)) % 12) + 1] for pos in positions]
    for category, positions in RASHI_PHALA_POSITIONS.items()
  }


def _shanti_note(nakshatra_index, rashi_index, script):
  nak_names = _shanti_nakshatra_names(nakshatra_index, script)
  rashi_phala = _rashi_phala_names(rashi_index, script)
  return (
    "Those with janma nakshatra %s (preceding/grahaNa/succeeding), or %s (anujanma) or %s (trijanma) "
    "get ashubha phala and should consider graha-shanti next day. "
    "By rashi: %s get more ashubha phala, %s somewhat ashubha, %s shubha phala." % (
      '/'.join(nak_names[0:3]), nak_names[3], nak_names[4],
      ', '.join(rashi_phala['more_ashubha']), ', '.join(rashi_phala['ashubha']), ', '.join(rashi_phala['shubha'])))


def _assemble(blurb, detailed_parts):
  return {
    'blurb': blurb,
    'detailed': ' '.join(detailed_parts),
    'image': '',
    'references': REFERENCE_NOTE,
    'url': '',
    'shlokas': '',
  }


def describe_solar_eclipse(grasta, suff, is_cudamani, attr, retflag, jd_contact_start, jd_contact_end, nakshatra_index,
                            rashi_index, tz, niyama_start_jd=None, general_note='', script=sanscript.ISO):
  """
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
  :param general_note: fixed do's/don'ts text (from a TOML rule) to append, or ''
  """
  node_en = NODE_NAMES[grasta]['en']
  ecl_type = _solar_eclipse_type(retflag)
  magnitude = attr[0]
  parimana_angula = magnitude * 12

  blurb = "%s solar eclipse (parimāṇa ≈%.1f of 12 aṅgulas), Sun at the %s. " % (
    ecl_type.capitalize(), parimana_angula, node_en)

  detailed = []
  note = _suffix_note(suff, ('sunrise', 'sunset'))
  if note is not None:
    detailed.append("The eclipse is %s." % note)
  detailed.append(
    "Magnitude: %.0f%% of the solar diameter is covered (parimāṇa ≈%.1f of the traditional 12 aṅgulas)." % (
      magnitude * 100, parimana_angula))
  if niyama_start_jd is None:
    niyama_start_jd = jd_contact_start - SOLAR_NIYAMA_HOURS_BEFORE_FALLBACK / 24.0
  niyama_text = Interval(jd_start=niyama_start_jd, jd_end=jd_contact_end, name='bhojana-niyama').to_hour_text(tz=tz, script=script)
  detailed.append("Avoid food: %s (from %d yaamas before the yaama of first contact, until the eclipse's end)." % (
    niyama_text, SOLAR_NIYAMA_YAAMAS_BEFORE))
  detailed.append(_shanti_note(nakshatra_index, rashi_index, script))
  if is_cudamani:
    detailed.append("Falling on a Sunday, this is an especially auspicious `cUDAmaNi` (crest-jewel) eclipse.")
  if general_note:
    detailed.append(general_note)

  return _assemble(blurb, detailed)


def describe_lunar_eclipse(grasta, suff, is_cudamani, attr, retflag, jd_contact_start, jd_contact_end, nakshatra_index,
                            rashi_index, tz, niyama_start_jd=None, general_note='', script=sanscript.ISO):
  """
  :param attr: the 20-tuple returned by swe.lun_eclipse_when_loc as its 3rd element
  :param retflag: the int retflag returned by swe.lun_eclipse_when_loc
  :param jd_contact_start: penumbral-begin JD (unclipped by moonrise/moonset)
  :param jd_contact_end: penumbral-end JD (unclipped by moonrise/moonset)
  :param nakshatra_index: 1-indexed nakshatra of the eclipsed Moon
  :param rashi_index: 1-indexed rashi of the eclipsed Moon
  :param niyama_start_jd: start of food restriction, yaama-aligned; falls back to a flat
    LUNAR_NIYAMA_HOURS_BEFORE_FALLBACK offset from jd_contact_start if None
  :param general_note: fixed do's/don'ts text (from a TOML rule) to append, or ''
  """
  node_en = NODE_NAMES[grasta]['en']
  ecl_type = _lunar_eclipse_type(retflag)
  magnitude = attr[0]  # umbral magnitude; can exceed 1.0 for total eclipses
  parimana_angula = min(magnitude, 1.0) * 12

  blurb = "%s lunar eclipse (parimāṇa ≈%.1f of 12 aṅgulas), Moon at the %s. " % (
    ecl_type.capitalize(), parimana_angula, node_en)

  detailed = []
  note = _suffix_note(suff, ('moonrise', 'moonset'))
  if note is not None:
    detailed.append("The eclipse is %s." % note)
  detailed.append(
    "Umbral magnitude: %.2f (parimāṇa ≈%.1f of the traditional 12 aṅgulas)." % (magnitude, parimana_angula))
  if niyama_start_jd is None:
    niyama_start_jd = jd_contact_start - LUNAR_NIYAMA_HOURS_BEFORE_FALLBACK / 24.0
  niyama_text = Interval(jd_start=niyama_start_jd, jd_end=jd_contact_end, name='bhojana-niyama').to_hour_text(tz=tz, script=script)
  detailed.append("Avoid food: %s (from %d yaamas before the yaama of first contact, until the eclipse's end)." % (
    niyama_text, LUNAR_NIYAMA_YAAMAS_BEFORE))
  detailed.append(_shanti_note(nakshatra_index, rashi_index, script))
  if is_cudamani:
    detailed.append("Falling on a Monday, this is an especially auspicious `cUDAmaNi` (crest-jewel) eclipse.")
  if general_note:
    detailed.append(general_note)

  return _assemble(blurb, detailed)
