import logging

from indic_transliteration import sanscript, xsanscript
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



def describe_fest(rule, include_images, include_shlokas, include_url, is_brief, script, truncate):
  # Get the Blurb
  blurb = get_timing_summary(rule)
  # Get the URL
  if include_url:
    url = rule.get_url()
  description_string = get_description_str_with_shlokas(include_shlokas, rule, script)
  if include_images:
    if rule.image is not None:
      image_string = '![](https://github.com/sanskrit-coders/adyatithi/blob/master/images/%s)\n\n' % rule.image
  ref_list = get_references_md(rule)
  # Now compose the description string based on the values of
  # include_url, include_images, is_brief
  if not is_brief:
    final_description_string = blurb
  else:
    if include_url:
      final_description_string = url
    else:
      final_description_string = ''
  final_description_string += description_string
  if include_images:
    final_description_string += image_string
  if truncate:
    if len(final_description_string) > 450:
      # Truncate
      final_description_string = '\n\n##### Details\n- [Edit config file](%s)\n- Tags: %s\n\n' % (url, ' '.join(default_if_none(rule.tags, [])))
  if not is_brief:
    final_description_string += ref_list
  if not is_brief and include_url:
    final_description_string += '\n\n##### Details\n- [Edit config file](%s)\n- Tags: %s\n\n' % (url, ' '.join(default_if_none(rule.tags, [])))
  return final_description_string


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
  description_items = sorted(descriptions.items(), key=lambda pair: ["en", "sa", "ta"].index(pair[0]))
  description_string = "\n\n".join([x[1] for x in description_items])
  if rule.shlokas is not None and include_shlokas:
    shlokas = xsanscript.transliterate(rule.shlokas.replace("\n", "  \n"), xsanscript.DEVANAGARI, script)
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
          pieces[i] = custom_transliteration.tr(piece, xsanscript.IAST, False)
      description_string = ''.join(pieces)
    else:
      logging.warning('Unmatched backquotes in description string: %s' % description_string)
  return description_string


def get_references_md(rule):
  ref_list = ''
  if rule.references_primary is not None or rule.references_secondary is not None:
    ref_list = '\n##### References\n'
    if rule.references_primary is not None:
      for ref in rule.references_primary:
        ref_list += '- %s\n' % transliterate_quoted_text(ref, sanscript.IAST)
    elif rule.references_secondary is not None:
      for ref in rule.references_secondary:
        ref_list += '- %s\n' % transliterate_quoted_text(ref, sanscript.IAST)
  return ref_list


def get_timing_summary(rule):
  if rule.timing is None:
    return ""
  blurb = ''
  month = ''
  angam = ''
  from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
  if rule.timing is not None and rule.timing.month_type is not None:
    month = ' of %s (%s) month' % (rule.timing.get_month_name_en(script=xsanscript.IAST), rule.timing.month_type.replace("_month", "").replace("_", " "))
  if rule.timing is not None and rule.timing.anga_type is not None:
    # logging.debug(rule.name)
    # if rule.name.startswith("ta:"):
    #   anga = custom_transliteration.tr(rule.name[3:], sanscript.TAMIL).replace("~", " ").strip("{}") + ' is observed on '
    # else:
    #   anga = custom_transliteration.tr(rule.name, sanscript.DEVANAGARI).replace("~", " ") + ' is observed on '
    angam = 'Observed on '

    if rule.timing.anga_type in ['tithi', 'yoga', 'nakshatra']:
      anga_type = AngaType.from_name(name=rule.timing.anga_type)
      angam += '%s %s' % (anga_type.names_dict[sanscript.IAST][rule.timing.anga_number], rule.timing.anga_type)
    elif rule.timing.anga_type == 'day':
      angam += 'day %d' % rule.timing.anga_number
  else:
    if rule.description is None:
      logging.debug("No anga_type in %s or description even!!", rule.id)

  if angam is not None:
    blurb += angam
  if month is not None:
    blurb += month
  if blurb != '':
    if rule.timing.month_type not in [RulesRepo.GREGORIAN_MONTH_DIR, RulesRepo.JULIAN_MONTH_DIR]:
      kaala = names.translate_or_transliterate(rule.timing.get_kaala(), script=xsanscript.IAST, source_script=xsanscript.DEVANAGARI)
      priority = rule.timing.get_priority()
      kaala_str = ' (%s/%s)' % (kaala, priority)
    else:
      kaala_str = ""
    blurb += "%s. " % kaala_str
    if rule.timing.julian_handling is not None:
      blurb += 'Julian date was %s in this reckoning. ' % (rule.timing.julian_handling)
    # logging.debug(blurb)
  if rule.timing.year_start is not None:
    blurb += "The event has been commemorated since it occurred in %s (%s era).  \n" % (rule.timing.year_start, rule.timing.year_start_era)
  return blurb
