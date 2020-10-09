import logging

from indic_transliteration import sanscript
from jyotisha import custom_transliteration
from jyotisha.names import get_chandra_masa, NAMES


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



def describe_fest(rule, include_images, include_shlokas, include_url, is_brief, script, truncate, use_markup):
  # Get the Blurb
  blurb = ''
  month = ''
  angam = ''
  if rule.timing is not None and rule.timing.month_type is not None:
    if rule.timing.month_type == 'lunar_month':
      if rule.timing.month_number == 0:
        month = ' of every lunar month'
      else:
        month = ' of ' + get_chandra_masa(rule.timing.month_number, NAMES, sanscript.IAST) + ' (lunar) month'
    elif rule.timing.month_type == 'sidereal_solar_month':
      if rule.timing.month_number == 0:
        month = ' of every solar month'
      else:
        month = ' of ' + NAMES['RASHI_NAMES'][sanscript.IAST][rule.timing.month_number] + ' (solar) month'
  if rule.timing is not None and rule.timing.anga_type is not None:
    # logging.debug(rule.name)
    # if rule.name.startswith("ta:"):
    #   anga = custom_transliteration.tr(rule.name[3:], sanscript.TAMIL).replace("~", " ").strip("{}") + ' is observed on '
    # else:
    #   anga = custom_transliteration.tr(rule.name, sanscript.DEVANAGARI).replace("~", " ") + ' is observed on '
    angam = 'Observed on '

    if rule.timing.anga_type == 'tithi':
      angam += NAMES['TITHI_NAMES'][sanscript.IAST][rule.timing.anga_number] + ' tithi'
    elif rule.timing.anga_type == 'nakshatra':
      angam += NAMES['NAKSHATRA_NAMES'][sanscript.IAST][rule.timing.anga_number] + ' nakṣhatram day'
    elif rule.timing.anga_type == 'day':
      angam += 'day %d' % rule.timing.anga_number
  else:
    if rule.description is None:
      logging.debug("No anga_type in %s or description even!!", rule.id)
  if rule.timing is not None and rule.timing.kaala is not None:
    kaala = rule.timing.kaala
  else:
    kaala = "sunrise (default)"
  if rule.timing is not None and rule.timing.priority is not None:
    priority = rule.timing.priority
  else:
    priority = 'puurvaviddha (default)'
  if angam is not None:
    blurb += angam
  if month is not None:
    blurb += month
  if blurb != '':
    blurb += ' (%s/%s).\n' % (kaala, priority)
    # logging.debug(blurb)
  # Get the URL
  if include_url:
    url = rule.get_url()
  # Get the description
  description_string = ''
  if rule.description is not None:
    # description_string = json.dumps(rule.description)
    description_string += rule.description["en"]
    pieces = description_string.split('`')
    if len(pieces) > 1:
      if len(pieces) % 2 == 1:
        # We much have matching backquotes, the contents of which can be neatly transliterated
        for i, piece in enumerate(pieces):
          if (i % 2) == 1:
            pieces[i] = custom_transliteration.tr(piece, script, False)
        description_string = ''.join(pieces)
      else:
        logging.warning('Unmatched backquotes in description string: %s' % description_string)
  if rule.shlokas is not None and include_shlokas:
    if use_markup:
      description_string = description_string + '\n\n```\n' + custom_transliteration.tr(", ".join(rule.shlokas),
                                                                                        script, False) + '\n```'
    else:
      description_string = description_string + '\n\n' + custom_transliteration.tr(", ".join(rule.shlokas), script,
                                                                                   False) + '\n\n'
  if include_images:
    if rule.image is not None:
      image_string = '![](https://github.com/sanskrit-coders/adyatithi/blob/master/images/%s)\n\n' % rule.image
  ref_list = ''
  if rule.references_primary is not None or rule.references_secondary is not None:
    ref_list = '\n### References\n'
    if rule.references_primary is not None:
      for ref in rule.references_primary:
        ref_list += '* %s\n' % transliterate_quoted_text(ref, sanscript.IAST)
    elif rule.references_secondary is not None:
      for ref in rule.references_secondary:
        ref_list += '* %s\n' % transliterate_quoted_text(ref, sanscript.IAST)
  # Now compose the description string based on the values of
  # include_url, include_images, use_markup, is_brief
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
      final_description_string = ' '.join(final_description_string[:450].split(' ')[:-1]) + ' ...\n'
  if not is_brief:
    final_description_string += ref_list
  if not is_brief and include_url:
    # if use_markup:
    final_description_string += ('\n\n%s\n' % url) + '\n' + ' '.join(['#' + x for x in rule.tags])
  # else:
  #   final_description_string += ('\n\n%s\n' % url) + '\n' + ' '.join(['#' + x for x in rule.tags])
  # if use_markup:
  #   final_description_string = final_description_string.replace('\n', '<br/><br/>')
  return final_description_string
