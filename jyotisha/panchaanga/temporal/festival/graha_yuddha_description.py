"""Dynamic description generation for graha-yuddha ("amshu-vimarda") festivals.

Like eclipses (see eclipse_description.py) and pushkaram, graha-yuddha festival ids are
combinatorial (10 unordered pairs among the 5 tArA grahas, each occurring an unpredictable
number of times a year with a different winner/loser/nakshatra/rashi each time), and every
individual occurrence differs in the exact positions, separation, and magnitudes involved.
Rather than a static per-combination TOML description (impossible here, since the combination
space isn't even enumerable in advance), this module builds the description directly from the
`details` dict already computed by
`EclipticFestivalAssigner.get_graha_yuddha_details`/`add_graha_yuddhas` at the moment of closest
approach.
"""
from jyotisha.panchaanga.temporal.body import Graha

GRAHA_NAMES_HK = {
  Graha.MERCURY: 'budhaH', Graha.VENUS: 'zukraH', Graha.MARS: 'aGgArakaH',
  Graha.JUPITER: 'guruH', Graha.SATURN: 'zaniH',
}

# Sourced from Brihat Samhita ch. 17 (as translated/cited in the accompanying Guru-Shani
# graha-yuddha pamphlet of 2020-Dec-21): significations specific to a *particular* graha pair,
# beyond what the pair-agnostic graha-yuddha-sAmAnya-niyamAH general note covers. Only populated
# for pairs we actually have sourced textual support for -- left empty (falls back to just the
# general note) for any pair not listed here, rather than guessing.
PAIR_NOTES = {
  frozenset({Graha.JUPITER, Graha.SATURN}): (
    "`bRhaspati` and `zanaizcara` (along with `budha`) are counted among the `paura` grahas "
    "(representing city-dwellers) in Brihat Samhita ch. 17; a yuddha between two `paura` grahas "
    "is said to indicate conflict between city-dwellers and their ruler. Classical commentary on "
    "this specific pair further associates `zanaizcara` prevailing with difficulties for "
    "brAhmaNas, and `bRhaspati` prevailing with difficulties for regions/groups with a large "
    "number of women -- though, as with any graha-yuddha, this is only ashubha-phala for a "
    "particular section of society, not a universal ill effect."
  ),
}


def _assemble(blurb, detailed, shlokas='', references='', url=''):
  return {
    'blurb': blurb,
    'detailed': detailed,
    'image': '',
    'references': references,
    'url': url,
    'shlokas': shlokas,
  }


def _format_dms(value_degrees):
  """Local copy of EclipticFestivalAssigner.format_dms -- kept independent of ecliptic.py to
  avoid a circular import (ecliptic.py imports this module, not the other way around)."""
  total_sec = abs(value_degrees) * 3600
  d = int(total_sec // 3600)
  m = int((total_sec % 3600) // 60)
  s = total_sec % 60
  return "%d°%02d′%05.2f″" % (d, m, s)


def _graha_position_text(graha, d):
  """One graha's position/motion/brightness clause, from a `details[graha]` sub-dict (see
  EclipticFestivalAssigner.get_graha_yuddha_details)."""
  return (
    "`%s` at `%s`-%d `%s` (latitude %s %s, %s, magnitude %+.2f, elongation %s %s)" % (
      GRAHA_NAMES_HK[graha], d['nakshatra'], d['pada'], d['rashi'],
      _format_dms(d['latitude']), d['lat_dir'],
      'vakra (retrograde)' if d['motion'] == 'vakra' else 'Rju (direct)',
      d['magnitude'],
      _format_dms(d['elongation']), d['elong_dir'])
  )


def describe_graha_yuddha(graha1, graha2, details, general_note='', shlokas='', pair_note=None):
  """
  :param graha1, graha2: Graha constants for the pair (any order -- `details` itself, from
    get_graha_yuddha_details, is keyed by these same two values)
  :param details: dict returned by EclipticFestivalAssigner.get_graha_yuddha_details at the
    moment (t_zero) of closest approach
  :param general_note: fixed do's/don'ts text (from the graha-yuddha-sAmAnya-niyamAH TOML rule)
    to append, or ''
  :param shlokas: the graha-yuddha-sAmAnya-niyamAH rule's own shlokas block (already
    transliterated to the target script by get_description_dict), or ''
  :param pair_note: sourced, pair-specific significations text to append (see PAIR_NOTES), or
    None to look it up automatically from PAIR_NOTES
  """
  if pair_note is None:
    pair_note = PAIR_NOTES.get(frozenset({graha1, graha2}), '')

  d1, d2 = details[graha1], details[graha2]
  disc_sep = details['disc_separation']
  winner, loser = details['winner'], details['loser']
  # The classical northern-graha criterion (see detailed text below) and the diameter/proximity
  # criterion this module (matching get_graha_yuddha_details' own convention) uses to name a
  # winner can disagree -- the north/south comparison below is reported as-is, independent of
  # which graha `details['winner']` actually names. Compare signed latitude (not just N/S sign),
  # since both grahas are commonly on the same side of the ecliptic (e.g. both North) -- what
  # matters here is which one is *more* north, not which hemisphere either happens to be in.
  lat1 = d1['latitude'] if d1['lat_dir'] == 'N' else -d1['latitude']
  lat2 = d2['latitude'] if d2['lat_dir'] == 'N' else -d2['latitude']
  north_graha = graha1 if lat1 > lat2 else (graha2 if lat2 > lat1 else None)

  is_true_yuddha = disc_sep < 0
  yuddha_prakara_label = "yuddha" if is_true_yuddha else "amshu-vimarda"
  yuddha_prakara_article = "a" if is_true_yuddha else "an"
  yuddha_prakara_gloss = "the discs actually overlap" if is_true_yuddha else \
    "a collision of rays -- the discs themselves do not touch"
  disc_sep_text = ("overlapping by %s" % _format_dms(disc_sep)) if is_true_yuddha \
    else "%s apart, disc-to-disc" % _format_dms(disc_sep)

  blurb = "Graha-yuddha (%s) between `%s` and `%s` in `%s` `%s`, center-to-center separation %s." % (
    yuddha_prakara_label, GRAHA_NAMES_HK[graha1], GRAHA_NAMES_HK[graha2], d1['nakshatra'], d1['rashi'],
    _format_dms(details['separation']))

  detailed = []
  detailed.append(
    "This is %s %s (%s): center-to-center separation %s, %s." % (
      yuddha_prakara_article, yuddha_prakara_label, yuddha_prakara_gloss, _format_dms(details['separation']), disc_sep_text))
  detailed.append("%s. %s." % (_graha_position_text(graha1, d1), _graha_position_text(graha2, d2)))
  if north_graha is not None:
    north_text = "`%s` is towards the north (traditionally said to prevail)" % GRAHA_NAMES_HK[north_graha]
  else:
    north_text = "the two are at essentially the same latitude, with neither clearly to the north of the other"
  detailed.append(
    "Classical texts weigh both the northern position and the greater apparent brightness/nearness "
    "in deciding the victor (jayI) of a yuddha; here %s, while by brightness/nearness (the larger "
    "apparent diameter) `%s` is taken as jayI over `%s`." % (
      north_text, GRAHA_NAMES_HK[winner], GRAHA_NAMES_HK[loser]))
  if pair_note:
    detailed.append(pair_note)
  if general_note:
    detailed.append(general_note)

  return _assemble(blurb, ' '.join(detailed), shlokas=shlokas)
