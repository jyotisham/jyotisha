""" The upAkarma nirNaya: a primary day, checked for flaws (doSa-s), with a veda-specific response to a flaw.

Moved here from the hand-coded `applier.upakarma.UpakarmaFestivalAssigner`; the behaviour is unchanged, but the
veda-specific facts (primary anga, fall-back days, governing graha, response to a flaw) now come from each
upAkarma's adyatithi entry instead of being hard-coded per festival id.

Why the generic engine can't do this: it keeps the *later* of two occurrences of an anga within the target month,
whereas upAkarma takes the *first*; and the flaw-driven fall-backs need to look beyond a single candidate day.

TOML (see the nirnaya package docstring for the general shape):

  [timing]
  month_type = "lunar_month"
  month_number = 5                 # primary: first occurrence in this (nija) lunar month of ...
  anga_type = "tithi"              # ... this anga ("tithi" or "nakshatra") ...
  anga_number = 15
  kaala = "मध्याह्नः"               # ... prevailing at this kaala, decided with this priority
  priority = "paraviddha"
  nirnaya = "upaakarma"

  [timing.nirnaya_options]
  maudhya_graha = "zukra"          # graha whose mAudhya/bAlya/vArdhakya is a flaw (guru, zukra, maGgala, ...)
  on_flaw = "chain"                # "chain" | "switch" | "keep" (see below)
  fallbacks = [                    # for "chain" and "switch": candidate days, each like the primary; anga_type,
    { month_number = 6 },          # anga_number, kaala and priority default to the primary's
    { month_number = 4 },
  ]

A flaw on a day is: an eclipse beginning before relative ghaTikA 45 of the day, a (sidereal solar) saGkramaNa on the
day ("hard" flaws, with no remedy), or mAudhya/bAlya/vArdhakya of `maudhya_graha` during the day ("soft").

on_flaw:
- "keep": use the primary day even if flawed.
- "switch": if the primary day is flawed, use the first fall-back, without checking it for flaws; if it can't be
  found, keep the primary.
- "chain": use the first unflawed day among [primary] + fallbacks. If all are flawed: when the primary's flaws are
  only soft, use the primary, also marking it `<id>~zAntipUrvakam` (mAudhya admits that expiatory remedy); else use
  the first fall-back that was found, accepting its flaws.
"""

import logging

from jyotisha.panchaanga.temporal import Anga, get_2_day_interval_boundary_angas
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import priority_decision
from jyotisha.panchaanga.temporal.festival.applier.ecliptic import BAALYA_VARDHAKYA_DAYS
from jyotisha.panchaanga.temporal.festival.nirnaya import NirnayaResult
from jyotisha.panchaanga.temporal.zodiac import AngaType

SHAANTI_SUFFIX = '~zAntipUrvakam'
COMPANION_SUFFIXES = [SHAANTI_SUFFIX]

GRAHA_BY_NAME = {
  'guru': Graha.JUPITER, 'bRhaspati': Graha.JUPITER, 'jupiter': Graha.JUPITER,
  'zukra': Graha.VENUS, 'venus': Graha.VENUS,
  'maGgala': Graha.MARS, 'aGgAraka': Graha.MARS, 'kuja': Graha.MARS, 'mars': Graha.MARS,
  'budha': Graha.MERCURY, 'mercury': Graha.MERCURY,
  'zani': Graha.SATURN, 'saturn': Graha.SATURN,
}

ANGA_TYPES = {'tithi': AngaType.TITHI, 'nakshatra': AngaType.NAKSHATRA}

ON_FLAW_VALUES = ('chain', 'switch', 'keep')

# "Eclipse before midnight" is read as: the eclipse begins before relative ghatikA 45 (ie. within the first half of
# the following night; ghatikA 30 is sunset, 60 is next sunrise) of the candidate day.
ECLIPSE_CUTOFF_RELATIVE_GHATIKA = 45


class Candidate(object):
  def __init__(self, month_number, anga_type, anga_number, kaala, priority):
    self.month_number = month_number
    self.anga_type = anga_type
    self.anga_number = anga_number
    self.kaala = kaala
    self.priority = priority

  def describe(self):
    return '%s-%s-%02d@%s' % (self.month_number, self.anga_type, self.anga_number, self.kaala)


def _get_candidates(rule):
  timing = rule.timing
  options = timing.nirnaya_options or {}
  primary = Candidate(month_number=timing.month_number, anga_type=timing.anga_type, anga_number=timing.anga_number,
                      kaala=timing.get_kaala(), priority=timing.get_priority())
  candidates = [primary]
  for fallback in options.get('fallbacks', []):
    candidates.append(Candidate(month_number=fallback.get('month_number', primary.month_number),
                                anga_type=fallback.get('anga_type', primary.anga_type),
                                anga_number=fallback.get('anga_number', primary.anga_number),
                                kaala=fallback.get('kaala', primary.kaala),
                                priority=fallback.get('priority', primary.priority)))
  return candidates


class UpaakarmaDecider(object):
  def __init__(self, assigner, rule):
    self.assigner = assigner
    self.panchaanga = assigner.panchaanga
    self.rule = rule
    options = rule.timing.nirnaya_options or {}
    graha_name = options.get('maudhya_graha', None)
    if graha_name not in GRAHA_BY_NAME:
      raise ValueError('%s: nirnaya_options.maudhya_graha must be one of %s, not %r' % (rule.id, sorted(GRAHA_BY_NAME), graha_name))
    self.graha = GRAHA_BY_NAME[graha_name]
    self.on_flaw = options.get('on_flaw', 'keep')
    if self.on_flaw not in ON_FLAW_VALUES:
      raise ValueError('%s: nirnaya_options.on_flaw must be one of %s, not %r' % (rule.id, ON_FLAW_VALUES, self.on_flaw))
    self.candidates = _get_candidates(rule)

  def first_occurrence_in_masa(self, candidate):
    """ Returns the Date of the *first* occurrence, within lunar masa `candidate.month_number`, of the candidate's
    anga prevailing at its kaala -- decided via the same puurvaviddha/paraviddha/vyaapti machinery
    (`festival.priority_decision`) the generic engine uses, but stopping at the first match within the masa
    instead of accumulating/overwriting with later ones.
    """
    anga_type = ANGA_TYPES[candidate.anga_type]
    kaala = candidate.kaala
    priority = candidate.priority
    target_anga = Anga.get_cached(index=candidate.anga_number, anga_type_id=anga_type.name)
    daily_panchaangas = self.assigner.daily_panchaangas
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = daily_panchaangas[d]
      if day_panchaanga.lunar_date.month.index != candidate.month_number:
        continue
      next_panchaanga = daily_panchaangas[d + 1]
      decision = priority_decision.decide(p0=day_panchaanga, p1=next_panchaanga, target_anga=target_anga,
                                          kaala=kaala, priority=priority, ayanaamsha_id=self.assigner.ayanaamsha_id)
      if decision is not None and priority in ('vyaapti', 'paraviddha') and decision.fday == 1:
        # decide() picked "tomorrow" (next_panchaanga) over "today" (day_panchaanga) based on just this pair. Since
        # an anga can never touch 3 consecutive days' kaalas, a look at the day after that settles whether
        # tomorrow's win is final: if the anga doesn't touch that day's kaala at all, tomorrow's win stands; if it
        # does, tomorrow's boundary match may just be the day-after's leading edge bleeding backwards (or a genuine
        # straddle continuing further) -- settle it directly by calling decide() on the (tomorrow, day-after) pair.
        # Mirrors the same look-ahead in `RuleLookupAssigner.apply_month_anga_events` (see the comment there);
        # omitting it is what caused zrAvaNa-pUrNimA 2027 to be mis-resolved as 08-16 instead of the correct 08-17.
        day_after_next = daily_panchaangas[d + 2]
        (_, day_after_next_angas) = get_2_day_interval_boundary_angas(kaala=kaala, anga_type=anga_type, p0=next_panchaanga, p1=day_after_next)
        if day_after_next_angas.start == target_anga or day_after_next_angas.end == target_anga:
          decision = priority_decision.decide(p0=next_panchaanga, p1=day_after_next, target_anga=target_anga,
                                              kaala=kaala, priority=priority, ayanaamsha_id=self.assigner.ayanaamsha_id)
      if decision is not None and decision.fday is not None and decision.fday != -1:
        return decision.day_panchaanga.date
    return None

  def _day_panchaanga(self, date):
    return self.panchaanga.date_str_to_panchaanga.get(date.get_date_str(), None)

  def has_eclipse_flaw(self, date):
    """ True iff a solar/lunar eclipse assigned to `date` (by `EclipticFestivalAssigner`, which must have already
    run) begins before relative ghatikA ECLIPSE_CUTOFF_RELATIVE_GHATIKA of that day. """
    day_panchaanga = self._day_panchaanga(date)
    if day_panchaanga is None:
      return False
    cutoff_jd = day_panchaanga.day_length_based_periods.fifteen_fold_division.get_relative_ghatika_interval(
      0, ECLIPSE_CUTOFF_RELATIVE_GHATIKA).jd_end
    for fest in day_panchaanga.festival_id_to_instance.values():
      if 'grahaNam' in fest.name and fest.interval is not None and fest.interval.jd_start is not None \
          and fest.interval.jd_start < cutoff_jd:
        return True
    return False

  def has_sankramana_flaw(self, date):
    """ True iff a (sidereal solar) saGkramaNa falls on `date` itself. """
    day_panchaanga = self._day_panchaanga(date)
    return day_panchaanga is not None and day_panchaanga.solar_sidereal_date_sunset.month_transition is not None

  def maudhya_intervals(self):
    # Cached on the assigner: the computation is expensive, and is shared by all upAkarma rules of one run.
    key = ('upaakarma.maudhya_intervals', self.graha)
    if key not in self.assigner.cache:
      from jyotisha.panchaanga.temporal.festival.applier.ecliptic import EclipticFestivalAssigner
      ecliptic_assigner = EclipticFestivalAssigner(panchaanga=self.panchaanga)
      # use_latitude=True: apply the akSAMza (observer-latitude, oblique-ascension) correction -- see
      # EclipticFestivalAssigner.compute_conjunction_intervals/add_maudhya_events, whose own docstrings establish
      # this as the empirically-validated convention for rise/set-relative mAudhya/bAlya/vArdhakya boundaries, for
      # every graha. Omitting it here silently used plain ecliptic-longitude boundaries instead, which can shift a
      # bAlya/vArdhakya edge by several days at higher latitudes and flip an upAkarma doSa check's verdict.
      self.assigner.cache[key] = ecliptic_assigner.compute_maudhya_intervals(
        self.graha, self.panchaanga.jd_start - 30, self.panchaanga.jd_end + 30, use_latitude=True)
    return self.assigner.cache[key]

  def has_maudhya_flaw(self, date):
    """ True iff the graha is in mAudhya (combust) at any point during the civil day `date`. """
    day_panchaanga = self._day_panchaanga(date)
    if day_panchaanga is None:
      return False
    flawed = any(mi.t_start <= day_panchaanga.jd_sunset and mi.t_end >= day_panchaanga.jd_sunrise
                 for mi in self.maudhya_intervals())
    if flawed:
      logging.info('%s mAudhya (combustion) flaw on %s.', self.graha, date.get_date_str())
    return flawed

  def has_baalya_vardhakya_flaw(self, date):
    """ True iff the graha is in bAlya (infancy) or vArdhakya (old age) -- the periods immediately flanking
    mAudhya, see BAALYA_VARDHAKYA_DAYS -- at any point during the civil day `date`. Only zukra/bRhaspati have these
    defined; other grahas never flag here. """
    days = BAALYA_VARDHAKYA_DAYS.get(self.graha)
    if days is None:
      return False
    day_panchaanga = self._day_panchaanga(date)
    if day_panchaanga is None:
      return False
    flawed = any(
      (mi.t_start - days['vardhakya'] <= day_panchaanga.jd_sunset and mi.t_start >= day_panchaanga.jd_sunrise) or
      (mi.t_end <= day_panchaanga.jd_sunset and mi.t_end + days['baalya'] >= day_panchaanga.jd_sunrise)
      for mi in self.maudhya_intervals())
    if flawed:
      logging.info('%s bAlya/vArdhakya flaw on %s.', self.graha, date.get_date_str())
    return flawed

  def has_hard_flaw(self, date):
    """ An eclipse before relative ghaTikA 45, or a saGkramaNa: neither admits the zAntipUrvakam remedy. """
    return date is not None and (self.has_eclipse_flaw(date) or self.has_sankramana_flaw(date))

  def has_flaw(self, date):
    return date is not None and (self.has_hard_flaw(date) or self.has_maudhya_flaw(date)
                                 or self.has_baalya_vardhakya_flaw(date))

  def decide(self):
    fest_id = self.rule.id
    if self.on_flaw == 'chain':
      return self._decide_chain()

    primary = self.first_occurrence_in_masa(self.candidates[0])
    if primary is None:
      return []
    if self.has_flaw(primary):
      if self.on_flaw == 'switch' and len(self.candidates) > 1:
        switched = self.first_occurrence_in_masa(self.candidates[1])
        if switched is not None:
          return [NirnayaResult(fest_id=fest_id, date=switched)]
        logging.warning('%s: primary date %s is flawed, but no switch date (%s) was found; keeping primary.',
                        fest_id, primary.get_date_str(), self.candidates[1].describe())
      else:
        logging.warning('%s on %s has an eclipse/saGkrAnti/mAudhya flaw, but no switch rule is defined for it; '
                        'keeping the primary date.', fest_id, primary.get_date_str())
    return [NirnayaResult(fest_id=fest_id, date=primary)]

  def _decide_chain(self):
    fest_id = self.rule.id
    chain_desc = '/'.join(c.describe() for c in self.candidates)
    dates = [self.first_occurrence_in_masa(c) for c in self.candidates]
    for date in dates:
      if date is not None and not self.has_flaw(date):
        return [NirnayaResult(fest_id=fest_id, date=date)]

    primary = dates[0]
    if primary is not None and not self.has_hard_flaw(primary):
      logging.info('%s: %s are all flawed; the primary candidate (%s) has only a mAudhya/bAlya/vArdhakya flaw, so '
                   'falling back to it, performed zAntipUrvakam.', fest_id, chain_desc, primary.get_date_str())
      return [NirnayaResult(fest_id=fest_id, date=primary), NirnayaResult(fest_id=fest_id + SHAANTI_SUFFIX, date=primary)]

    for date in dates[1:]:
      if date is not None:
        logging.info('%s: %s are all flawed, and the primary candidate (%s) itself has an eclipse/saGkrAnti flaw (no '
                     'zAntipUrvakam remedy for that) -- falling through to %s.',
                     fest_id, chain_desc, primary.get_date_str() if primary else None, date.get_date_str())
        return [NirnayaResult(fest_id=fest_id, date=date)]

    logging.error('%s: could not resolve a date -- all of %s were either not found or flawed, with no fallback '
                  'available.', fest_id, chain_desc)
    return []


def decide(assigner, rule):
  return UpaakarmaDecider(assigner=assigner, rule=rule).decide()
