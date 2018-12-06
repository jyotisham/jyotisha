import json
import logging
import os

from sanskrit_data.schema.common import JsonObject
from jyotisha import custom_transliteration
from jyotisha.panchangam.spatio_temporal import CODE_ROOT
# from jyotisha.panchangam.temporal import festival
from jyotisha.panchangam.temporal.festival import HinduCalendarEventOld, HinduCalendarEvent
from jyotisha.panchangam.temporal import get_chandra_masa, NAMES
from indic_transliteration import xsanscript as sanscript

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def migrate_db(old_db_file):
  old_style_events = HinduCalendarEventOld.read_from_file(old_db_file)
  # TODO: Reset all README files in the folder here?
  for old_style_event in old_style_events:
    event = HinduCalendarEvent.from_old_style_event(old_style_event=old_style_event)
    logging.debug(str(event))
    event_file_name = event.get_storage_file_name(base_dir=os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data'))
    logging.debug(event_file_name)
    event.dump_to_file(filename=event_file_name)
    write_event_README(event, event_file_name)


# TODO:
# Should this be moved to another file?
# Should be called as event.write_README()??
def write_event_README(event, event_file_name):
    with open(event_file_name) as event_data:
      readme_file_name = os.path.join(os.path.dirname(event_file_name), 'README.md')
      event_dict = json.load(event_data)
      with open(readme_file_name, 'a+') as readme_file:
        readme_file.write('## %s\n' % event_dict["id"].replace('ta__', '').replace('~', ' '))

        blurb = ''
        month = ''
        angam = ''
        if 'month_type' in event_dict['timing']:
            if event_dict['timing']['month_type'] == 'lunar_month':
                month = ' of ' + get_chandra_masa(event_dict['timing']['month_number'], NAMES, sanscript.IAST) + ' (lunar) month'
            elif event_dict['timing']['month_type'] == 'solar_month':
                month = ' of ' + NAMES['RASHI_NAMES'][sanscript.IAST][event_dict['timing']['month_number']] + ' (solar) month'
        if 'angam_type' in event_dict['timing']:
            logging.debug(event_dict["id"])
            if event_dict["id"][:4] == "ta__":
              angam = custom_transliteration.tr(event_dict["id"][4:], sanscript.TAMIL) + ' is observed on '
            else:
              angam = custom_transliteration.tr(event_dict["id"], sanscript.DEVANAGARI).replace("~", " ") + ' is observed on '

            if event_dict['timing']['angam_type'] == 'tithi':
                angam += NAMES['TITHI_NAMES'][sanscript.IAST][event_dict['timing']['angam_number']] + ' tithi'
            elif event_dict['timing']['angam_type'] == 'nakshatram':
                angam += NAMES['NAKSHATRAM_NAMES'][sanscript.IAST][event_dict['timing']['angam_number']] + ' nakṣhatram day'
            elif event_dict['timing']['angam_type'] == 'day':
                angam += 'day %d' % event_dict['timing']['angam_number']
        else:
          logging.debug('No angam_type in %s', event_dict['id'])
        if 'kaala' in event_dict['timing']:
          kaala = event_dict["timing"]["kaala"]
        else:
          kaala = "sunrise (default)"
        if 'priority' in event_dict:
          priority = event_dict["priority"]
        else:
          priority = 'puurvaviddha (default)'
        if angam is not None:
            blurb += angam
        if month is not None:
            blurb += month
        if blurb != '':
            blurb += ' (%s/%s).\n\n' % (kaala, priority)
        readme_file.write(blurb)
        description_string = ""
        logging.debug(event_dict)
        if "description" in event_dict:
          # description_string = json.dumps(event_dict.description)
          description_string = '_' + event_dict["description"]["en"] + '_'
        if "shlokas" in event_dict:
          description_string = description_string + '\n\n' + \
                               custom_transliteration.tr(", ".join(event_dict["shlokas"]),
                                                         sanscript.DEVANAGARI, False)
        readme_file.write(description_string)
        if "references_primary" in event_dict or "references_secondary" in event_dict:
          readme_file.write('\n')
          readme_file.write('### References\n')
          if "references_primary" in event_dict:
            for ref in event_dict["references_primary"]:
              readme_file.write('* %s\n' % ref)
          elif "references_secondary" in event_dict:
            for ref in event_dict["references_secondary"]:
              readme_file.write('* %s\n' % ref)
        readme_file.write('\n\n---\n')


def migrate_relative_db():
  old_style_events = HinduCalendarEventOld.read_from_file(os.path.join(CODE_ROOT, 'panchangam/data/relative_festival_rules.json'))
  for old_style_event in old_style_events:
    event = HinduCalendarEvent.from_old_style_event(old_style_event=old_style_event)
    logging.debug(str(event))
    event_file_name = event.get_storage_file_name(base_dir=os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data'))
    logging.debug(event_file_name)
    event.dump_to_file(filename=event_file_name)


def legacy_dict_to_HinduCalendarEventOld_list(old_db_file, new_db_file):
  with open(old_db_file, 'r') as f:
    legacy_event_dict = json.load(f)
  old_style_events = []
  for id, legacy_event in legacy_event_dict.items():
    event_old_style = HinduCalendarEventOld.from_legacy_event(id, legacy_event)
    old_style_events.append(event_old_style)
  json_map_list = JsonObject.get_json_map_list(old_style_events)
  with open(new_db_file, 'w') as f:
    json.dump(json_map_list, f, indent=4, sort_keys=True)


if __name__ == '__main__':
  # legacy_dict_to_HinduCalendarEventOld_list(os.path.join(CODE_ROOT, 'panchangam/data/legacy/festival_rules.json'), os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
  # legacy_dict_to_HinduCalendarEventOld_list(os.path.join(CODE_ROOT, 'panchangam/data/legacy/festival_rules_desc_only.json'), os.path.join(CODE_ROOT, 'panchangam/data/festival_rules_desc_only.json'))
  # legacy_dict_to_HinduCalendarEventOld_list(os.path.join(CODE_ROOT, 'panchangam/data/legacy/relative_festival_rules.json'), os.path.join(CODE_ROOT, 'panchangam/data/relative_festival_rules.json'))
  migrate_db(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
  # migrate_db(os.path.join(CODE_ROOT, 'panchangam/data/kanchi_aradhana_rules.json'))
  migrate_relative_db()
  pass
