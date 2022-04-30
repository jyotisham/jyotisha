import codecs
import logging
import os
import sys
from pathlib import Path

import methodtools
import regex
import toml
from curation_utils import file_helper
from sanskrit_data import collection_helper
from timebudget import timebudget

from jyotisha import custom_transliteration
from jyotisha.panchaanga.temporal import names
from sanskrit_data.schema import common
from indic_transliteration import sanscript

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


def clean_id(id):
  id = id.replace('/','__').strip('{}')
  id = regex.sub(" +", "_", id)
  return id


def inverse_clean_id(id):
  id = id.replace('__', '/')
  id = regex.sub("_", " ", id)
  return id


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

  def get_storage_file_name_flat(self, base_dir):
    return "%(base_dir)s/%(id)s.toml"  % dict(
      base_dir=base_dir,
      id=self.id
    )

  def get_storage_file_name(self, base_dir, undo_conversions):
    if self.timing.anchor_festival_id is not None:
      path = "relative_event/%(anchor_festival_id)s/offset__%(offset)02d/%(id)s.toml" % dict(
        anchor_festival_id=self.timing.anchor_festival_id.replace('/','__'),
        offset=self.timing.offset,
        id=self.id
      )
    elif self.timing is None or self.timing.month_number is None:
      path = "description_only/%(id)s.toml" % dict(
        id=self.id
      )
    else:
      try:
        month_type = self.timing.month_type
        anga_type = self.timing.anga_type
        month_number = self.timing.month_number
        anga_number = self.timing.anga_number
        if undo_conversions:
          if self.timing.julian_handling == RulesCollection.JULIAN_TO_GREGORIAN:
            from jyotisha.panchaanga.temporal import time
            jul_date = time.Date.to_julian_date(year=self.timing.year_start, month=self.timing.month_number, day=self.timing.anga_number)
            anga_number = jul_date.day
            month_number = jul_date.month
            month_type = RulesRepo.JULIAN_MONTH_DIR
        path = "%(month_type)s/%(anga_type)s/%(month_number)02d/%(anga_number)02d/%(id)s.toml" % dict(
          month_type=month_type,
          anga_type=anga_type,
          month_number=month_number,
          anga_number=anga_number,
          id=self.id
        )
      except Exception:
        logging.error(str(self))
        raise 
    if base_dir.startswith("http"):
      from urllib.parse import quote
      path = quote(path)  
    return "%s/%s" % (base_dir, path)

  def get_url(self):
    encoded_url = self.get_storage_file_name(base_dir=self.repo.base_url, undo_conversions=True)
    # https://github.com/jyotisham/jyotisha/runs/1229399248?check_suite_focus=true shows that ~ is being replaced there, which breaks tests. Hence the below.
    return encoded_url.replace("%7E", "~")

  def get_description_string(self, script, include_url=False, include_images=False, 
                             include_shlokas=False, is_brief=False, truncate=False, header_md="#####"):
    from jyotisha.panchaanga.temporal.festival.rules import summary
    final_description_string = summary.describe_fest(self, include_images, include_shlokas, include_url, is_brief, script,
    truncate, header_md=header_md)

    return final_description_string

  def get_description_dict(self, script):
    from jyotisha.panchaanga.temporal.festival.rules import summary

    description_dict = {}

    description_dict['blurb'] = summary.get_timing_summary(self)
    description_dict['detailed'] = summary.get_description_str_with_shlokas(False, self, script)
    if self.image is None:
      description_dict['image'] = ''
    else:
      description_dict['image'] = self.image

    description_dict['references'] = summary.get_references_md(self)
    
    description_dict['url'] = summary.get_url(self)

    if self.shlokas is not None:
      description_dict['shlokas'] = sanscript.transliterate(self.shlokas.replace("\n", "  \n"), sanscript.DEVANAGARI, script)
    else:
      description_dict['shlokas'] = ''

    return description_dict

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
_ADYATITHI_REPOS_PATH = os.path.join(DATA_ROOT, "repos.toml")


class RulesRepo(common.JsonObject):
  LUNAR_MONTH_DIR = "lunar_month"
  SIDEREAL_SOLAR_MONTH_DIR = "sidereal_solar_month"
  TROPICAL_MONTH_DIR = "tropical"
  GREGORIAN_MONTH_DIR = "gregorian"
  ISLAMIC_MONTH_DIR = "islamic"
  JULIAN_MONTH_DIR = "julian"
  RELATIVE_EVENT_DIR = "relative_event"
  DAY_DIR = "day"
  TITHI_DIR = "tithi"
  NAKSHATRA_DIR = "nakshatra"
  YOGA_DIR = "yoga"

  def __init__(self, name, path=None, base_url='https://github.com/jyotisham/adyatithi/blob/master'):
    super().__init__()
    self.name = name
    self.path = path
    self.base_url = os.path.join(base_url, name)

  def get_path(self):
    #  We don't set the path in __init__ so as to avoid storing machine-specific paths for canonical repos_tuple.
    return self.path if self.path is not None else os.path.join(DATA_ROOT, self.name)


class RulesCollection(common.JsonObject):
  JULIAN_AS_GREGORIAN = "treated as Gregorian"
  JULIAN_TO_GREGORIAN = "converted to Gregorian"


  def __init__(self, repos, julian_handling=JULIAN_TO_GREGORIAN):
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
        os.path.join(DATA_ROOT, repo.get_path()), julian_handling=None, repo=repo)
      for rule in rules_map.values():
        rule.path_actual = None
        rule.repo = None
        rule.dump_to_file(filename=rule.get_storage_file_name(base_dir=base_dir, undo_conversions=True))

  def fix_filenames(self):
    for repo in self.repos:
      base_dir = repo.get_path()
      rules_map = get_festival_rules_map(
        os.path.join(DATA_ROOT, repo.get_path()), repo=repo, julian_handling=None)
      for rule in rules_map.values():
        update_path = False
        old_id = rule.id
        rule.id = clean_id(rule.id)
        update_path = update_path or old_id != rule.id
        if rule.timing.anchor_festival_id is not None:
          old_id = rule.timing.anchor_festival_id
          rule.timing.anchor_festival_id = clean_id(rule.timing.anchor_festival_id)
          update_path = update_path or old_id != rule.timing.anchor_festival_id
        expected_path = rule.get_storage_file_name(base_dir=base_dir, undo_conversions=True)
        update_path = update_path or rule.path_actual != expected_path
        if update_path:
          logging.info(str((rule.path_actual, expected_path)))
          os.remove(str(rule.path_actual))
          rule.path_actual = None
          rule.repo = None
          rule.dump_to_file(filename=rule.get_storage_file_name(base_dir=base_dir, undo_conversions=True))
          # os.makedirs(os.path.dirname(expected_path), exist_ok=True)
      file_helper.remove_empty_dirs(path=os.path.join(DATA_ROOT, repo.get_path()))

  @timebudget
  def set_rule_dicts(self, julian_handling):
    for repo in self.repos:
      self.name_to_rule.update(get_festival_rules_map(
        os.path.join(DATA_ROOT, repo.get_path()), repo=repo, julian_handling=julian_handling))

    from sanskrit_data import collection_helper
    self.tree = collection_helper.tree_maker(leaves=self.name_to_rule.values(), path_fn=lambda x: x.get_storage_file_name(base_dir="", undo_conversions=False).replace(".toml", ""))

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
      subtree = self.tree[month_type.lower()][anga_type_id.lower()][month_str]["%02d" % anga]
      tree_out = {}
      for x, y in subtree.items():
        if x != collection_helper.LEAVES_KEY:
          tree_out[x] = y[collection_helper.LEAVES_KEY][0]
      return tree_out
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


# The below is filled by load_repos() below.
rule_repos = ()


def dump_repos():
  repos = [repo.to_json_map() for repo in rule_repos]
  repos.sort(key=lambda x: x["name"])
  with codecs.open(_ADYATITHI_REPOS_PATH, "w") as fp:
    toml.dump({"data": repos}, fp)


def load_repos():
  """
  
  common.update_json_class_index should be called before calling this. 
  :return: 
  """
  global rule_repos
  with codecs.open(_ADYATITHI_REPOS_PATH, "r") as fp:
    repos = toml.load(fp)
    rule_repos = tuple(common.JsonObject.make_from_dict_list(repos["data"]))


load_repos()

if __name__ == '__main__':
  # dump_repos()
  rules_collection = RulesCollection.get_cached(repos_tuple=rule_repos, julian_handling=None)
  # rules_collection = RulesCollection(repos=[RulesRepo(name="mahApuruSha/xatra-later")], julian_handling=None)
  rules_collection.fix_filenames()
  # rules_collection.fix_content()

