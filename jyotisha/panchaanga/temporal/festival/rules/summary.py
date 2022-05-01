import logging

import regex

from indic_transliteration import sanscript
from jyotisha import custom_transliteration
from jyotisha.panchaanga.temporal import AngaType, names
from jyotisha.util import default_if_none


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



def describe_fest(rule, include_images, include_shlokas, include_url, is_brief, script, truncate, header_md="#####"):
  # Get the Blurb
  blurb = get_timing_summary(rule)
  # Get the URL
  description_string = get_description_str_with_shlokas(include_shlokas, rule, script)
  description_string = regex.sub("\n##", "\n%s" % header_md, "\n" + description_string).lstrip()
  if include_images:
    if rule.image is not None:
      image_string = '![](https://github.com/jyotisham/adyatithi/blob/master/images/%s)\n\n' % rule.image
  # Now compose the description string based on the values of
  # include_url, include_images, is_brief
  if not is_brief:
    final_description_string = blurb
  else:
      final_description_string = ''
  final_description_string += "\n\n" + description_string
  if include_images:
    final_description_string += image_string
  url = rule.get_url()
  if truncate:
    if len(final_description_string) > 450:
      # Truncate
      final_description_string = '\n\n%s Details\n- [Edit config file](%s)\n- Tags: %s\n\n' % (header_md, url, ' '.join(default_if_none(rule.tags, [])))
  if not is_brief:
    ref_list = get_references_md(rule)
    final_description_string += '\n\n%s Details\n%s- [Edit config file](%s)\n- Tags: %s\n\n' % (header_md, ref_list, url, ' '.join(default_if_none(rule.tags, [])))
  return final_description_string


def get_url(rule):
  return rule.get_url()


def get_description_str_with_shlokas(include_shlokas, rule, script):
  # Get the description
  description_string = ''
  descriptions = {}
  if rule.description is not None:
    # description_string = json.dumps(rule.description)
    for language in rule.description:
      if language == "en":
        descriptions["en"] = get_english_description(description_string, rule)
      else:
        descriptions[language] = rule.description[language]
  description_items = sorted(descriptions.items(), key=lambda pair: {"en": 0, "sa": 1, "ta": 2, "kn": 3}.get(pair[0], 99))
  description_string = "\n\n".join([x[1].strip() for x in description_items])
  if rule.shlokas is not None and include_shlokas:
    shlokas = sanscript.transliterate(rule.shlokas.strip().replace("\n", "  \n"), sanscript.DEVANAGARI, script)
    description_string = description_string + '\n\n' + shlokas + '\n\n'
  return description_string


def get_english_description(description_string, rule):
  if "en" not in rule.description:
    return ""
  description_string += rule.description["en"]
  pieces = description_string.split('`')
  if len(pieces) > 1:
    if len(pieces) % 2 == 1:
      # We much have matching backquotes, the contents of which can be neatly transliterated
      for i, piece in enumerate(pieces):
        if (i % 2) == 1:
          pieces[i] = custom_transliteration.tr(piece, sanscript.ISO, False)
      description_string = ''.join(pieces)
    else:
      logging.warning('Unmatched backquotes in description string: %s' % description_string)
  return description_string


def get_references_md(rule):
  ref_list = ''
  if rule.references_primary is not None or rule.references_secondary is not None:
    ref_list = '- References\n'
    if rule.references_primary is not None:
      for ref in rule.references_primary:
        ref_list += '  - %s\n' % transliterate_quoted_text(ref, sanscript.ISO)
    elif rule.references_secondary is not None:
      for ref in rule.references_secondary:
        ref_list += '  - %s\n' % transliterate_quoted_text(ref, sanscript.ISO)
  return ref_list


def get_timing_summary(rule):
  if rule.timing is None:
    return ""
  blurb = ''
  month = ''
  angam = ''
  from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
  if rule.timing is not None and rule.timing.month_type is not None:
    if rule.timing.month_type in ['julian', 'gregorian'] and rule.timing.year_start is not None:
      blurb = "Event occured on %04d-%02d-%02d (%s). " % (rule.timing.year_start, rule.timing.month_number, rule.timing.anga_number, rule.timing.month_type)
      if rule.timing.julian_handling is not None:
        blurb += 'Julian date was %s in this reckoning. ' % (rule.timing.julian_handling)
      return blurb
    month = ' of %s (%s) month' % (rule.timing.get_month_name_en(script=sanscript.ISO), rule.timing.month_type.replace("_month", "").replace("_", " "))
    if rule.timing.month_number == 0:
      if rule.timing.anga_type in ['yoga', 'nakshatra']:
        month = ''
        angam = 'every occurrence of '
  if rule.timing is not None and rule.timing.anga_type is not None:
    if rule.timing.anga_type in ['tithi', 'yoga', 'nakshatra']:
      angam = 'Observed on ' + angam
      anga_type = AngaType.from_name(name=rule.timing.anga_type)
      angam += '%s %s' % (anga_type.names_dict[sanscript.ISO][rule.timing.anga_number], rule.timing.anga_type)
    elif rule.timing.anga_type == 'day':
      angam = 'Observed on ' + angam
      angam += 'day %d' % rule.timing.anga_number
  else: # No timing or anga_type
    if rule.description is None:
      logging.warning("No anga_type in %s or description even!!", rule.id)

  if angam is not None:
    blurb += angam
  if month is not None:
    blurb += month
  if blurb != '':
    if rule.timing.month_type not in [RulesRepo.GREGORIAN_MONTH_DIR, RulesRepo.JULIAN_MONTH_DIR]:
      kaala = names.translate_or_transliterate(rule.timing.get_kaala(), script=sanscript.ISO, source_script=sanscript.DEVANAGARI)
      priority = rule.timing.get_priority()
      kaala_str = ' (%s/%s)' % (kaala, priority)
    else:
      kaala_str = ""
    blurb += "%s. " % kaala_str
    # logging.debug(blurb)
  if rule.timing.year_start is not None:
    blurb += "The event occurred in %s (%s era).  \n" % (rule.timing.year_start, rule.timing.year_start_era.capitalize())
  return blurb
