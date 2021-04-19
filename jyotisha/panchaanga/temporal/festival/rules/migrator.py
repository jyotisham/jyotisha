import logging

from indic_transliteration import sanscript
from jyotisha.panchaanga.temporal import era
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo, HinduCalendarEventTiming, HinduCalendarEvent


def import_to_xaatra_later():
  import toml
  input_path = ""
  events_in = toml.load(input_path)
  repo = RulesRepo(name="mahApuruSha/xatra-later")
  for event in events_in["data"]:
    logging.debug(event)
    from jyotisha.panchaanga.temporal.time import Date
    timing = HinduCalendarEventTiming()
    if "Gregorian date" in event:
      date_str = event["Gregorian date"]
      timing.month_type = RulesRepo.GREGORIAN_MONTH_DIR
    else:
      date_str = event["Julian date"]
      timing.month_type = RulesRepo.JULIAN_MONTH_DIR
    dt = Date.from_string(date_str)
    timing.anga_type = RulesRepo.DAY_DIR
    timing.month_number = dt.month
    timing.anga_number = dt.day
    timing.year_start = dt.year
    timing.year_start_era = era.ERA_GREGORIAN
    rule = HinduCalendarEvent()
    rule.timing = timing
    rule.id = event["name_sa"].replace(" ", "_")
    en_description = " ".join([event["tithi"], event["Incident"], event["Other notes"]])
    rule.description = {"en": en_description.strip()}
    rule.names = {"sa": [sanscript.transliterate(data=event["name_sa"], _from=sanscript.OPTITRANS, _to=sanscript.DEVANAGARI)]}
    rule.dump_to_file(filename=rule.get_storage_file_name(base_dir=repo.get_path(), undo_conversions=True))