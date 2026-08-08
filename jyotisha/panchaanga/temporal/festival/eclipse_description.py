"""Dynamic description generation for eclipse ("grahaNa") festivals.

Eclipse festival ids are combinatorial (node x grastOdaya/grastAstamana/plain
x cUDAmaNi), and every individual occurrence differs in magnitude and timing.
Rather than maintaining a static TOML description file per combination (which
also forces every eclipse of a given "type" to share one canned description,
regardless of how partial/total/long it actually was), this module builds the
description directly from the astronomical circumstances of each occurrence,
computed by ecliptic.py at the time the festival instance is created.

Sūtaka timing follows the common Dharmasindhu/Nirṇayasindhu rule (starts a
fixed interval before first contact, ends at the eclipse's last contact).
This is a widely cited approximation, not a fixed pan-tradition rule; treat
it as such. Determining which janma-nakshatras call for graha-śānti is not
attempted here -- it needs a specific classical source/table, which hasn't
been pinned down yet.
"""
import swisseph as swe
from indic_transliteration import sanscript

from jyotisha.panchaanga.temporal.interval import Interval

NODE_NAMES = {
  'rAhumukhagrast': dict(en='Rahu node (ascending/mukha)'),
  'rAhupucchagrast': dict(en='Ketu node (descending/puccha)'),
}

# Widely-cited approximation (Dharmasindhu/Nirnayasindhu): sutaka begins a
# fixed interval before first contact and ends at the eclipse's last
# contact. Regional/sectarian practice varies (e.g. some traditions waive
# sutaka for eclipses that are not visible from the location); this is not
# accounted for here.
SOLAR_SUTAKA_HOURS_BEFORE = 12
LUNAR_SUTAKA_HOURS_BEFORE = 9

SUTAKA_REFERENCE_NOTE = (
  "- References\n"
  "  - Sūtaka window shown uses the common 12h(solar)/9h(lunar)-before-first-contact rule "
  "(Dharmasindhu/Nirṇayasindhu); regional and sectarian practice varies.\n"
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
    return "still in progress at %s (grastāstamana)" % rise_or_set_word[1]
  return None


def _assemble(blurb, detailed_parts):
  return {
    'blurb': blurb,
    'detailed': ' '.join(detailed_parts),
    'image': '',
    'references': SUTAKA_REFERENCE_NOTE,
    'url': '',
    'shlokas': '',
  }


def describe_solar_eclipse(grasta, suff, is_cudamani, attr, retflag, jd_contact_start, jd_contact_end, tz, script=sanscript.ISO):
  """
  :param grasta: 'rAhumukhagrast' or 'rAhupucchagrast'
  :param suff: 'a' (plain), 'Odaya' (grastodaya) or 'Astamana' (grastAstamana)
  :param attr: the 20-tuple returned by swe.sol_eclipse_when_loc as its 3rd element
  :param retflag: the int retflag returned by swe.sol_eclipse_when_loc
  :param jd_contact_start: first-contact JD (unclipped by sunrise/sunset)
  :param jd_contact_end: last-contact JD (unclipped by sunrise/sunset)
  :param tz: a Timezone instance, for rendering the sutaka window
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
  sutaka_start_jd = jd_contact_start - SOLAR_SUTAKA_HOURS_BEFORE / 24.0
  sutaka_text = Interval(jd_start=sutaka_start_jd, jd_end=jd_contact_end, name='sUtaka').to_hour_text(tz=tz, script=script)
  detailed.append("Sūtaka (approx.): %s — begins %dh before first contact, ends at the eclipse's end." % (
    sutaka_text, SOLAR_SUTAKA_HOURS_BEFORE))
  if is_cudamani:
    detailed.append("Falling on a Sunday, this is an especially auspicious `cUDAmaNi` (crest-jewel) eclipse.")

  return _assemble(blurb, detailed)


def describe_lunar_eclipse(grasta, suff, is_cudamani, attr, retflag, jd_contact_start, jd_contact_end, tz, script=sanscript.ISO):
  """
  :param attr: the 20-tuple returned by swe.lun_eclipse_when_loc as its 3rd element
  :param retflag: the int retflag returned by swe.lun_eclipse_when_loc
  :param jd_contact_start: penumbral-begin JD (unclipped by moonrise/moonset)
  :param jd_contact_end: penumbral-end JD (unclipped by moonrise/moonset)
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
  sutaka_start_jd = jd_contact_start - LUNAR_SUTAKA_HOURS_BEFORE / 24.0
  sutaka_text = Interval(jd_start=sutaka_start_jd, jd_end=jd_contact_end, name='sUtaka').to_hour_text(tz=tz, script=script)
  detailed.append("Sūtaka (approx.): %s — begins %dh before first contact, ends at the eclipse's end." % (
    sutaka_text, LUNAR_SUTAKA_HOURS_BEFORE))
  if is_cudamani:
    detailed.append("Falling on a Monday, this is an especially auspicious `cUDAmaNi` (crest-jewel) eclipse.")

  return _assemble(blurb, detailed)
