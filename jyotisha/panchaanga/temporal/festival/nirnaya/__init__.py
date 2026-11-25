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
  `<id>~zAntipUrvakam`) on `date`, optionally restricted to `interval_id` (a named interval of that day, as accepted
  by DailyPanchaanga.get_interval; defaults to the full day, as for every other festival). """

  def __init__(self, fest_id, date, interval_id="full_day"):
    self.fest_id = fest_id
    self.date = date
    self.interval_id = interval_id


def get_procedures():
  """ Procedure name (the TOML `nirnaya` value) -> its module. Each module defines `decide(assigner, rule)` and
  `COMPANION_SUFFIXES`: suffixes of qualified ids (`<id><suffix>`) it may emit besides the rule's own id.
  Imported lazily, since procedure modules import applier helpers. """
  from jyotisha.panchaanga.temporal.festival.nirnaya import upaakarma
  return {
    "upaakarma": upaakarma,
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
        self.panchaanga.add_festival(fest_id=result.fest_id, date=result.date, interval_id=result.interval_id)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
