import logging
import os
import sys
from pathlib import Path

import methodtools
from timebudget import timebudget

from jyotisha import custom_transliteration
from jyotisha.panchaanga.temporal import names
from sanskrit_data.schema import common


def transliterate_quoted_text(text, script):
  transliterated_text = text
  pieces = transliterated_text.split('`')
  if len(pieces) > 1:
    if len(pieces) % 2 == 1:
      # We much have matching backquotes, the contents of which can be neatly transliterated
      for i, piece in enumerate(pieces):
        if (i % 2) == 1:
          pieces[i] = custom_transliteration.tr(piece, script, titled=True)
      transliterated_text = ''.join(pieces)
    else:
      logging.warning('Unmatched backquotes in string: %s' % transliterated_text)
  return transliterated_text



class HinduCalendarEventTiming(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEventTiming"]
      },
      "month_type": {
        "type": "string",
        "enum": ["lunar_month", "sidereal_solar_month", "tropical_month"],
        "description": "",
      },
      "month_number": {
        "type": "integer",
        "description": "",
      },
      "anga_type": {
        "type": "string",
        "enum": ["tithi", "nakshatra", "yoga", "day"],
        "description": "",
      },
      "anga_number": {
        "type": "integer",
        "description": "",
      },
      "kaala": {
        "type": "string",
        "description": "",
      },
      "priority": {
        "type": "string",
        "description": "",
      },
      "year_start": {
        "type": "integer",
        "description": "",
      },
      "anchor_festival_id": {
        "type": "string",
        "description": "A festival may be (say) 8 days before some other event xyz. The xyz is stored here.",
      },
      "offset": {
        "type": "integer",
        "description": "A festival may be 8 days before some other event xyz. The 8 is stored here.",
      },
    }
  }))

  def __init__(self, month_type, month_number, anga_type, anga_number, kaala, year_start):
    self.month_type = month_type
    self.month_number = month_number
    self.anga_type = anga_type
    self.anga_number = anga_number
    self.kaala = kaala
    self.year_start = year_start
    self.anchor_festival_id = None
    self.offset = None
    self.julian_handling = None

  def get_kaala(self):
    return "सूर्योदयः" if self.kaala is None else self.kaala

  def get_priority(self):
    return "puurvaviddha" if self.priority is None else self.priority
    
  def get_month_name_en(self, script):
    return names.get_month_name_en(month_type=self.month_type, month_number=self.month_number, script=script)

# noinspection PyUnresolvedReferences
class HinduCalendarEvent(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEvent"]
      },
      "timing": HinduCalendarEventTiming.schema,
      "tags": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
      },
      "comments": {
        "type": "string",
        "description": "",
      },
      "image": {
        "type": "string",
        "description": "",
      },
      "description": {
        "type": "object",
        "description": "Language code to text mapping.",
      },
      "names": {
        "type": "object",
        "description": "Language code to text array mapping.",
      },
      "shlokas": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "references_primary": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "references_secondary": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
    }
  }))
  
  def __init__(self, id):
    self.id = id
    self.timing = None
    self.tags = None
    self.references_primary = None
    self.references_secondary = None
    self.names = None
    self.description = None
    self.image = None
    self.path_actual = None

  def get_storage_file_name(self, base_dir):
    return self.get_storage_file_name_granular(base_dir=base_dir)

  def get_storage_file_name_flat(self, base_dir):
    return "%(base_dir)s/%(id)s.toml"  % dict(
      base_dir=base_dir,
      id=self.id.replace('/','__').strip('{}')
    )

  def get_storage_file_name_granular(self, base_dir):
    if self.timing.anchor_festival_id is not None:
      path = "relative_event/%(anchor_festival_id)s/offset__%(offset)02d/%(id)s.toml" % dict(
        anchor_festival_id=self.timing.anchor_festival_id.replace('/','__'),
        offset=self.timing.offset,
        id=self.id.replace('/','__').strip('{}')
      )
    elif self.timing is None or self.timing.month_number is None:
      path = "description_only/%(id)s.toml" % dict(
        id=self.id.replace('/','__').strip('{}')
      )
    else:
      try:
        path = "%(month_type)s/%(anga_type)s/%(month_number)02d/%(anga_number)02d/%(id)s.toml" % dict(
          month_type=self.timing.month_type,
          anga_type=self.timing.anga_type,
          month_number=self.timing.month_number,
          anga_number=self.timing.anga_number,
          id=self.id.replace('/','__').strip('{}')
        )
      except Exception:
        logging.error(str(self))
        raise 
    if base_dir.startswith("http"):
      from urllib.parse import quote
      path = quote(path)
    return "%s/%s" % (base_dir, path)

  def get_url(self):
    # encoded_url = "https://" + quote(self.path_actual.replace(self.repo.path, self.repo.base_url.replace("https://", "")))
    encoded_url = self.get_storage_file_name(base_dir=self.repo.base_url)
    # https://github.com/sanskrit-coders/jyotisha/runs/1229399248?check_suite_focus=true shows that ~ is being replaced there, which breaks tests. Hence the below.
    return encoded_url.replace("%7E", "~")

  def get_description_string(self, script, include_url=False, include_images=False, 
                             include_shlokas=False, is_brief=False, truncate=False):
    from jyotisha.panchaanga.temporal.festival.rules import summary
    final_description_string = summary.describe_fest(self, include_images, include_shlokas, include_url, is_brief, script,
    truncate)

    return final_description_string

  def to_gregorian(self, julian_handling):
    if self.timing.month_type != RulesRepo.JULIAN_MONTH_DIR:
      return 
    if julian_handling == RulesCollection.JULIAN_TO_GREGORIAN:
      from jyotisha.panchaanga.temporal import time 
      greg_date = time.Date.from_julian_date(year=self.timing.year_start, month=self.timing.month_number, day=self.timing.anga_number)
      self.timing.julian_handling = julian_handling
      self.timing.anga_number = greg_date.day
      self.timing.month_number = greg_date.month
      self.timing.month_type = RulesRepo.GREGORIAN_MONTH_DIR
    elif julian_handling == RulesCollection.JULIAN_AS_GREGORIAN:
      self.timing.julian_handling = julian_handling
      self.timing.month_type = RulesRepo.GREGORIAN_MONTH_DIR
      


def get_festival_rules_map(dir_path, julian_handling, repo=None):
  toml_file_paths = sorted(Path(dir_path).glob("**/*.toml"))
  festival_rules = {}
  if len(toml_file_paths) == 0:
    logging.warning("No festival rule found at %s", dir_path)
    return festival_rules
  for file_path in toml_file_paths:
    event = HinduCalendarEvent.read_from_file(filename=str(file_path))
    event.path_actual = str(file_path)
    event.repo = repo
    event.to_gregorian(julian_handling=julian_handling)
    festival_rules[event.id] = event
  return festival_rules


DATA_ROOT = os.path.join(os.path.dirname(__file__), "../data")


class RulesRepo(common.JsonObject):
  LUNAR_MONTH_DIR = "lunar_month"
  SIDEREAL_SOLAR_MONTH_DIR = "sidereal_solar_month"
  TROPICAL_MONTH_DIR = "tropical"
  GREGORIAN_MONTH_DIR = "gregorian"
  JULIAN_MONTH_DIR = "julian"
  RELATIVE_EVENT_DIR = "relative_event"
  ERA_GREGORIAN = "gregorian"
  ERA_KALI = "kali"
  DAY_DIR = "day"
  TITHI_DIR = "tithi"
  NAKSHATRA_DIR = "nakshatra"
  YOGA_DIR = "yoga"

  def __init__(self, name, path=None, base_url='https://github.com/sanskrit-coders/adyatithi/tree/master'):
    super().__init__()
    self.name = name
    self.path = path
    self.base_url = os.path.join(base_url, name)

  def get_path(self):
    #  We don't set the path in __init__ so as to avoid storing machine-specific paths for canonical repos_tuple.
    return self.path if self.path is not None else os.path.join(DATA_ROOT, self.name)


rule_repos = (RulesRepo(name="general"), RulesRepo(name="gRhya/general"), RulesRepo(name="gRhya/Apastamba"), RulesRepo(name="tamil"), RulesRepo(name="mahApuruSha/general"), RulesRepo(name="devatA/pitR"), RulesRepo(name="devatA/shaiva"), RulesRepo(name="devatA/umA"), RulesRepo(name="devatA/graha"), RulesRepo(name="devatA/nadI"), RulesRepo(name="devatA/shakti"), RulesRepo(name="devatA/gaNapati"),  RulesRepo(name="devatA/kaumAra"),  RulesRepo(name="devatA/vaiShNava"), RulesRepo(name="devatA/lakShmI"), RulesRepo(name="devatA/misc-fauna"), RulesRepo(name="devatA/misc-flora"), RulesRepo(name="mahApuruSha/kAnchI-maTha"), RulesRepo(name="mahApuruSha/ALvAr"), RulesRepo(name="mahApuruSha/vaiShNava-misc"), RulesRepo(name="mahApuruSha/mAdhva-misc"), RulesRepo(name="mahApuruSha/smArta-misc"), RulesRepo(name="mahApuruSha/sangIta-kRt"), RulesRepo(name="mahApuruSha/xatra"), RulesRepo(name="mahApuruSha/xatra-later"), RulesRepo(name="mahApuruSha/RShi"), RulesRepo(name="mahApuruSha/nAyanAr"), RulesRepo(name="temples/venkaTAchala"), RulesRepo(name="temples/Andhra"), RulesRepo(name="temples/Tamil"), RulesRepo(name="temples/Kerala"), RulesRepo(name="temples/Odisha"), RulesRepo(name="temples/North"), RulesRepo(name="time_focus/sankrAnti"), RulesRepo(name="time_focus/puShkara"), RulesRepo(name="time_focus/yugAdiH"), RulesRepo(name="time_focus/misc"),  RulesRepo(name="time_focus/Rtu"), RulesRepo(name="time_focus/nakShatra"), RulesRepo(name="time_focus/Eclipses"), RulesRepo(name="time_focus/misc_combinations"), RulesRepo(name="time_focus/monthly/amAvAsyA"), RulesRepo(name="time_focus/monthly/ekAdashI"), RulesRepo(name="time_focus/monthly/dvAdashI"), RulesRepo(name="time_focus/monthly/pradoSha"),)


class RulesCollection(common.JsonObject):
  JULIAN_AS_GREGORIAN = "treated as Gregorian"
  JULIAN_TO_GREGORIAN = "converted to Gregorian"


  def __init__(self, repos=rule_repos, julian_handling=JULIAN_TO_GREGORIAN):
    super().__init__()
    self.repos = repos
    self.name_to_rule = {}
    self.tree = None 
    self.set_rule_dicts(julian_handling=julian_handling)

  @methodtools.lru_cache()  # the order is important!
  @classmethod
  def get_cached(cls, repos_tuple, julian_handling=JULIAN_TO_GREGORIAN):
    return RulesCollection(repos=repos_tuple, julian_handling=julian_handling)

  def fix_content(self):
    for repo in self.repos:
      base_dir = repo.get_path()
      rules_map = get_festival_rules_map(
        os.path.join(DATA_ROOT, repo.get_path(), julian_handling=None), repo=repo)
      for rule in rules_map.values():
        if rule.shlokas is not None:
          rule.shlokas = rule.shlokas.replace("\\n", "  \n")
        rule.path_actual = None
        rule.repo = None
        rule.dump_to_file(filename=rule.get_storage_file_name(base_dir=base_dir))

  def fix_filenames(self):
    for repo in self.repos:
      base_dir = repo.get_path()
      rules_map = get_festival_rules_map(
        os.path.join(DATA_ROOT, repo.get_path(), julian_handling=None), repo=repo)
      for rule in rules_map.values():
        expected_path = rule.get_storage_file_name(base_dir=base_dir)
        if rule.path_actual != expected_path:
          logging.info(str((rule.path_actual, expected_path)))
          os.makedirs(os.path.dirname(expected_path), exist_ok=True)
          os.rename(rule.path_actual, expected_path)

  @timebudget
  def set_rule_dicts(self, julian_handling):
    for repo in self.repos:
      self.name_to_rule.update(get_festival_rules_map(
        os.path.join(DATA_ROOT, repo.get_path()), repo=repo, julian_handling=julian_handling))

    from sanskrit_data import collection_helper
    self.tree = collection_helper.tree_maker(leaves=self.name_to_rule.values(), path_fn=lambda x: x.get_storage_file_name_granular(base_dir="").replace(".toml", ""))

  def get_month_anga_fests(self, month_type, month, anga_type_id, anga):
    if int(month) != month:
      # Deal with adhika mAsas
      month_str = "%02d.5" % month
    else:
      month_str = "%02d" % month
    from jyotisha.panchaanga.temporal.zodiac import Anga
    if isinstance(anga, Anga):
      anga = anga.index
    try:
      return self.tree[month_type.lower()][anga_type_id.lower()][month_str]["%02d" % anga]
    except KeyError:
      return {}

  def get_possibly_relevant_fests(self, month_type, month, anga_type_id, angas):
    fest_dict = {}
    for anga in angas:
      from jyotisha.panchaanga.temporal.zodiac.angas import Tithi
      if isinstance(anga, Tithi) and month_type == RulesRepo.LUNAR_MONTH_DIR:
        month = anga.month.index
      for m in [month, 0]:
        fest_dict.update(self.get_month_anga_fests(month_type=month_type, month=m, anga_type_id=anga_type_id, anga=anga))
    return fest_dict


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


if __name__ == '__main__':
  rules_collection = RulesCollection.get_cached(repos_tuple=rule_repos, julian_handling=None)
  rules_collection = RulesCollection(repos=[RulesRepo(name="mahApuruSha/xatra-later")], julian_handling=None)
  # rules_collection.fix_filenames()
  # rules_collection.fix_content()
