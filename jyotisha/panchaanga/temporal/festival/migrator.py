import json
import logging
import os

from indic_transliteration import xsanscript as sanscript

from jyotisha import custom_transliteration
from jyotisha.names import get_chandra_masa, NAMES
# from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal.festival.rules import HinduCalendarEvent, HinduCalendarEventOld
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


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


def migrate_db(old_db_file, only_descriptions=False):
  old_style_events = HinduCalendarEventOld.read_from_file(old_db_file)
  output_dir = os.path.join(os.path.dirname(__file__), 'data')
  # import shutil
  # shutil.rmtree(output_dir)
  for old_style_event in old_style_events:
    event = HinduCalendarEvent.from_old_style_event(old_style_event=old_style_event)
    logging.debug(str(event))
    event_file_name = event.get_storage_file_name(base_dir=output_dir, only_descriptions=only_descriptions)
    logging.debug(event_file_name)
    event.dump_to_file(filename=event_file_name)
    # append_to_event_group_README(event, event_file_name)


# TODO: Broken.
# Should this be moved to another file?
# Should be called as event.write_README()??
def append_to_event_group_README(event, event_file_name):
  event_dict = JsonObject.read_from_file(event_file_name)
  readme_file_name = os.path.join(os.path.dirname(event_file_name), 'README.md')
  # # Clear the README first.
  # with open(readme_file_name, 'w') as readme_file:
  #   readme_file.write("")
  with open(readme_file_name, 'a') as readme_file:
    headline = custom_transliteration.tr(event_dict["id"], sanscript.IAST).replace('Ta__', '').replace('~',
                                                                                                       ' ').strip(
      '{}')
    # Replace letter following r̂/r̂r̂ with lowercase
    for sep in ['r̂']:
      if headline[1:].find(sep) != -1:
        headline = sep.join([word[0].lower() + word[1:] for word in headline.split(sep)])
        headline = headline[0].upper() + headline[1:]
    for sep in ['r̂r̂']:
      if headline[1:].find(sep) != -1:
        headline = sep.join([word[0].lower() + word[1:] for word in headline.split(sep)])
        headline = headline[0].upper() + headline[1:]
    readme_file.write('## %s\n' % headline)

    blurb = ''
    month = ''
    angam = ''
    if 'month_type' in event_dict['timing']:
      if event_dict['timing']['timing']['month_type'] == 'lunar_month':
        if event_dict['timing']['timing']['month_number'] == 0:
          month = ' of every lunar month'
        else:
          month = ' of ' + get_chandra_masa(event_dict['timing']['timing']['month_number'], NAMES,
                                            sanscript.IAST) + ' (lunar) month'
      elif event_dict['timing']['timing']['month_type'] == 'solar_month':
        if event_dict['timing']['timing']['month_number'] == 0:
          month = ' of every solar month'
        else:
          month = ' of ' + NAMES['RASHI_NAMES'][sanscript.IAST][
            event_dict['timing']['timing']['month_number']] + ' (solar) month'
    if 'angam_type' in event_dict['timing']:
      logging.debug(event_dict["id"])
      if event_dict["id"][:4] == "ta__":
        angam = custom_transliteration.tr(event_dict["id"][4:], sanscript.TAMIL).replace("~", " ").strip(
          "{}") + ' is observed on '
      else:
        angam = custom_transliteration.tr(event_dict["id"], sanscript.DEVANAGARI).replace("~",
                                                                                          " ") + ' is observed on '

      if event_dict['timing']['timing']['angam_type'] == 'tithi':
        angam += NAMES['TITHI_NAMES'][sanscript.IAST][event_dict['timing']['angam_number']] + ' tithi'
      elif event_dict['timing']['timing']['angam_type'] == 'nakshatram':
        angam += NAMES['NAKSHATRAM_NAMES'][sanscript.IAST][event_dict['timing']['angam_number']] + ' nakṣhatram day'
      elif event_dict['timing']['timing']['angam_type'] == 'day':
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
    if "image" in event_dict:
      description_string = '![](https://github.com/sanskrit-coders/adyatithi/blob/master/images/%s)\n\n' % event_dict[
        'image']

    if "description" in event_dict:
      # description_string = json.dumps(event_dict.description)
      # description_string = '_' + event_dict["description"]["en"] + '_'
      description_string = description_string + '_' + event.get_description_string(script=sanscript.DEVANAGARI) + '_'
    if "shlokas" in event_dict:
      description_string = description_string + '\n\n```\n' + \
                           custom_transliteration.tr(", ".join(event_dict["shlokas"]),
                                                     sanscript.DEVANAGARI, False) + '\n```'
    readme_file.write(description_string)
    if "references_primary" in event_dict or "references_secondary" in event_dict:
      readme_file.write('\n')
      readme_file.write('### References\n')
      if "references_primary" in event_dict:
        for ref in event_dict["references_primary"]:
          readme_file.write('* %s\n' % transliterate_quoted_text(ref, sanscript.IAST))
      if "references_secondary" in event_dict:
        for ref in event_dict["references_secondary"]:
          readme_file.write('* %s\n' % transliterate_quoted_text(ref, sanscript.IAST))
    readme_file.write('\n\n---\n')


def migrate_relative_db():
  old_style_events = HinduCalendarEventOld.read_from_file(
    filename = os.path.join(os.path.dirname(__file__), 'data/legacy/relative_festival_rules.json'))
  for old_style_event in old_style_events:
    event = HinduCalendarEvent.from_old_style_event(old_style_event=old_style_event)
    logging.debug(str(event))
    event_file_name = event.get_storage_file_name(base_dir=os.path.join(os.path.dirname(__file__), 'data'))
    logging.debug(event_file_name)
    event.dump_to_file(filename=event_file_name)
    # append_to_event_group_README(event, event_file_name)


def legacy_dict_to_HinduCalendarEventOld_list(old_db_file, new_db_file):
  with open(old_db_file, 'r') as f:
    legacy_event_dict = json.load(f)
  old_style_events = []
  for id, legacy_event in legacy_event_dict.items():
    event_old_style = HinduCalendarEventOld.from_legacy_event(id, legacy_event)
    old_style_events.append(event_old_style)
  json_map_list = JsonObject.get_json_map_list(old_style_events)
  with open(new_db_file, 'w') as f:
    json.dump(json_map_list, f, indent=2, sort_keys=True)


def clear_output_dirs():
  import shutil
  for dir in ["lunar_month", "other", "relative_event", "solar_month"]:
    shutil.rmtree(os.path.join(os.path.dirname(__file__), 'data', dir), ignore_errors=True)


if __name__ == '__main__':
  clear_output_dirs()
  migrate_db(os.path.join(os.path.dirname(__file__), 'data/legacy/festival_rules.json'))
  migrate_db(os.path.join(os.path.dirname(__file__), 'data/legacy/festival_rules_desc_only.json'), only_descriptions=True)
  migrate_relative_db()
  pass
