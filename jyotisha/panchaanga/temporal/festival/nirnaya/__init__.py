""" Named decision procedures (nirNaya-s) for festivals whose day cannot be decided by the generic rule engine.

A festival rule (an adyatithi TOML entry) opts in by naming a procedure in its timing:

  [timing]
  month_type = "lunar_month"      # the primary month/anga/kaala/priority, read by the procedure
  month_number = 5
  anga_type = "tithi"
  anga_number = 15
  kaala = "मध्याह्नः"
  priority = "paraviddha"
  nirnaya = "upaakarma"           # a key of PROCEDURES below

  [timing.nirnaya_options]        # procedure-specific parameters (see each procedure's docstring)
  ...

Such a rule is stored at `[repo]/nirnaya/[id].toml` (see HinduCalendarEvent.get_storage_file_name), so none of the
generic engines in `applier.rule_repo_based` sees it: the named procedure alone decides its date(s). Rules without
`nirnaya` are untouched by this module.

This is for *deciders* -- one festival, one (possibly elaborate) decision. *Generators* -- code that derives a
whole family of festival ids from one computation (ekAdazI variants, mahAdvAdazI-s, anadhyayana days, ...) -- stay
in their own appliers and never go through here.

A procedure is a module (registered in get_procedures) with a function `decide(assigner, rule) -> list of
NirnayaResult`, where `assigner` is the
NirnayaFestivalAssigner (giving access to the panchaanga, its daily panchaangas and shared helpers) and `rule` the
HinduCalendarEvent. It must not add festivals itself; the dispatcher adds what it returns.
"""

import logging
import sys

from sanskrit_data.schema import common

from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner


class NirnayaResult(object):
  """ One decided festival occurrence: `fest_id` (the rule's own id, or a qualified companion of it such as
  `<id>~zAntipUrvakam`) on `date`. Optionally, `interval` (an Interval) is the time on that day the procedure chose
  (eg. a bhadrA-free muhUrta), shown with the festival; else `interval_id` names an interval of that day, as accepted
  by DailyPanchaanga.get_interval (default: the full day, as for every other festival). """

  def __init__(self, fest_id, date, interval_id="full_day", interval=None):
    self.fest_id = fest_id
    self.date = date
    self.interval_id = interval_id
    self.interval = interval


def find_tithi_spans(assigner, month_number, tithi_index):
  """ Each occurrence of `tithi_index` in (nija) lunar month `month_number` that begins on a day of the panchaanga
  proper (not its padding): [(d, jd_start, jd_end)], where d indexes assigner.daily_panchaangas and is the civil day
  (sunrise to next sunrise) in which the tithi begins. The days after d are always available (the panchaanga is padded
  after its end), so a procedure may look at d + 1 and d + 2. """
  from jyotisha.panchaanga.temporal.zodiac import AngaSpanFinder, Ayanamsha
  from jyotisha.panchaanga.temporal.zodiac.angas import AngaType
  finder = AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=AngaType.TITHI)
  panchaanga = assigner.panchaanga
  spans = []
  for d in range(panchaanga.duration_prior_padding, panchaanga.duration + panchaanga.duration_prior_padding):
    day = assigner.daily_panchaangas[d]
    for span in finder.get_all_angas_in_period(jd1=day.jd_sunrise, jd2=day.jd_next_sunrise):
      if span.anga.index != tithi_index or span.jd_start is None or not (day.jd_sunrise <= span.jd_start < day.jd_next_sunrise):
        continue
      if day.lunar_date.month.index != month_number:
        continue
      full_span = finder.find(jd1=span.jd_start - 0.1, jd2=span.jd_start + 3, target_anga_id=tithi_index)
      spans.append((d, span.jd_start, full_span.jd_end))
  return spans


def get_procedures():
  """ Procedure name (the TOML `nirnaya` value) -> its module. Each module defines `decide(assigner, rule)` and
  `COMPANION_SUFFIXES`: suffixes of qualified ids (`<id><suffix>`) it may emit besides the rule's own id.
  Imported lazily, since procedure modules import applier helpers. """
  from jyotisha.panchaanga.temporal.festival.nirnaya import upaakarma, holikaa, rakshaabandhana
  return {
    "upaakarma": upaakarma,
    "holikaa": holikaa,
    "rakshaabandhana": rakshaabandhana,
  }


class NirnayaFestivalAssigner(FestivalAssigner):
  def __init__(self, panchaanga):
    super().__init__(panchaanga=panchaanga)
    # Scratch space shared by the procedures during one assign_all() run (eg. mAudhya intervals per graha, which
    # are expensive and common to several upAkarma rules).
    self.cache = {}

  def get_nirnaya_rules(self):
    fest_rules = [rule for rule in self.rules_collection.name_to_rule.values()
                  if rule.timing is not None and rule.timing.nirnaya is not None]
    return sorted(fest_rules, key=lambda rule: rule.id)

  def assign_all(self):
    procedures = get_procedures()
    for rule in self.get_nirnaya_rules():
      procedure = procedures.get(rule.timing.nirnaya, None)
      if procedure is None:
        logging.error('%s: unknown nirnaya procedure %r (known: %s); not assigning it.', rule.id,
                      rule.timing.nirnaya, sorted(procedures))
        continue
      for suffix in [''] + list(procedure.COMPANION_SUFFIXES):
        self.panchaanga.delete_festival(fest_id=rule.id + suffix)
      for result in procedure.decide(self, rule):
        self.panchaanga.add_festival(fest_id=result.fest_id, date=result.date, interval_id=result.interval_id,
                                     interval=result.interval)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
