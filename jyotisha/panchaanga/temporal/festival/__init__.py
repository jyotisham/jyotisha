import logging
import re
import sys

from indic_transliteration import sanscript, language_code_to_script
from jyotisha import custom_transliteration
from jyotisha.util import default_if_none
from sanskrit_data.schema import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

festival_id_to_json = {}


class FestivalInstance(common.JsonObject):
  def __init__(self, name, interval=None, ordinal=None, exclude=None, description=None, names=None):
    super(FestivalInstance, self).__init__()
    self.name = name
    self.interval = interval
    self.exclude = exclude
    self.ordinal = ordinal
    # Optional pre-computed description dict (keys: blurb, detailed, image,
    # references, url, shlokas), for festivals whose description depends on
    # the specific occurrence (e.g. eclipses) rather than just the festival
    # id, and is therefore computed by the applier at creation time instead
    # of being looked up from a TOML rule by name. When set, this takes
    # precedence over any TOML-based lookup.
    self.description = description
    # Optional pre-computed human names dict (e.g. {"sa": ["चन्द्र-ग्रहणम्~(केतुग्रस्त)"]}),
    # for the same class of festival as `description` above -- without this,
    # get_human_names() falls back to auto-transliterating the raw fest_id,
    # which is accurate but loses any curated/idiomatic naming.
    self.names = names

  def get_detailed_name_with_timings(self, timezone, reference_date=None):
    name = self.name

    if self.ordinal is not None:
      name = name + " #%s" % int(self.ordinal)

    if self.interval is None or self._show_interval() is False:
      return name
    else:
      return "%s (%s)" % (name, self.interval.to_hour_text(script=sanscript.ISO, tz=timezone, reference_date=reference_date))

  def get_human_names(self, fest_details_dict):
    if self.names is not None:
      import copy
      return copy.deepcopy(self.names)
    from jyotisha.panchaanga.temporal.festival import rules
    fest_details = fest_details_dict.get(self.name, rules.HinduCalendarEvent(id=self.name))
    if fest_details.names is None:
      sa_name = sanscript.transliterate(self.name.replace("~", " "), sanscript.roman.HK_DRAVIDIAN, sanscript.DEVANAGARI, togglers={'##'})
      sa_name = rules.inverse_clean_id(sa_name)
      fest_details.names = {"sa": [sa_name]}
    import copy
    names = copy.deepcopy(fest_details.names)
    return names

  def get_best_transliterated_name(self, languages, scripts, fest_details_dict):
    names = self.get_human_names(fest_details_dict=fest_details_dict)
    for language in languages:
      if language in names.keys():
        if language_code_to_script[language] in scripts:
          transliterated_text = custom_transliteration.transliterate_from_language(language=language, text=names[language][0], script=language_code_to_script[language])
          return {"script": language_code_to_script[language], "text": transliterated_text}
        else:
          transliterated_text = custom_transliteration.transliterate_from_language(language=language, text=names[language][0], script=scripts[0])
          return {"script": scripts[0], "text": transliterated_text}

    # No language text matching the input scripts was found.
    if "sa" in names:
      language = "sa"
    else:
      language = list(names.keys())[0]
    transliterated_text = custom_transliteration.transliterate_from_language(language=language, text=names[language][0], script=scripts[0])
    return {"script": scripts[0], "text": transliterated_text}

  def tex_code(self, languages, scripts, timezone, fest_details_dict, reference_date=None, time_format='hh:mm'):
    name_details = self.get_best_transliterated_name(languages=languages, scripts=scripts, fest_details_dict=fest_details_dict)
    if name_details["script"] == sanscript.TAMIL:
      name = '\\tamil{%s}' % name_details["text"]
    else:
      name = name_details["text"]

    if self.ordinal is not None:
      name = name + "~\\#{%s}" % custom_transliteration.tr(str(self.ordinal), script=scripts[0])

    if self.interval is not None and self._show_interval():
      return "%s%s" % (name, self.interval.to_hour_tex(script=scripts[0], tz=timezone, reference_date=reference_date, time_format=time_format))
    else:
      return name

  def get_full_title(self, fest_details_dict, languages=["sa"], scripts=[sanscript.DEVANAGARI]):
    name_details = self.get_best_transliterated_name(languages=languages, scripts=scripts, fest_details_dict=fest_details_dict)
    ordinal_str = " #%s" % custom_transliteration.tr(str(self.ordinal), script=name_details["script"]) if self.ordinal is not None else ""
    return "%s%s" % (name_details["text"].replace("~", "-"), ordinal_str)

  def md_code(self, languages, scripts, timezone, fest_details_dict, header_md):
    title = self.get_full_title(languages=languages, scripts=scripts, fest_details_dict=fest_details_dict)
    heading = "%s %s" % (header_md, title)
    if self.interval is None or  not self._show_interval():
      md = heading
    else:
      start_time_str = "" if self.interval.jd_start is None else timezone.julian_day_to_local_time(self.interval.jd_start).get_hour_str()
      end_time_str = "" if self.interval.jd_end is None else timezone.julian_day_to_local_time(self.interval.jd_end).get_hour_str()
      md = "%s\n- %s→%s" % (heading, start_time_str, end_time_str)
    description = get_description(festival_instance=self, fest_details_dict=fest_details_dict, script=scripts[0], truncate=False, header_md="#" + header_md)
    if description != "":
      md = "%s\n\n%s" % (md, description)
    return md

  def _show_interval(self):
    if self.interval.jd_start is None and self.interval.jd_end is None:
      return False

    if self.interval.jd_start is not None and self.interval.jd_end is not None and self.interval.get_jd_length() > 0.9:
      long_festivals_list = ['SaDazIti', 'puSkara-yOga', 'gajacchAyA-yOgaH'] # phrases that can be used to map to long festivals
      if not any(fest_name in self.name for fest_name in long_festivals_list):
        return False

    return True

  def __lt__(self, other):
    return self.name < other.name

  def __hash__(self):
    return hash(self.name)

  def __repr__(self):
    return "%s %s %s" % (self.name, str(default_if_none(self.ordinal, "")), str(default_if_none(self.interval, "")))


class TransitionFestivalInstance(FestivalInstance):
  def __init__(self, name, status_1_hk, status_2_hk, interval):
    super(TransitionFestivalInstance, self).__init__(name=name)
    self.status_1_hk = status_1_hk
    self.status_2_hk = status_2_hk
    self.interval = interval

  def tex_code(self, languages, scripts, timezone, fest_details_dict, reference_date=None, time_format='hh:mm'):
    name_details = self.get_best_transliterated_name(languages=languages, scripts=scripts, fest_details_dict=fest_details_dict)
    name = name_details["text"]
    if self.interval is not None and self._show_interval():
      return custom_transliteration.tr("%s~(%s##\\To{}##%s)" % (name, self.status_1_hk, self.status_2_hk), script=scripts[0]) + "%s" % (self.interval.to_hour_tex(script=scripts[0], tz=timezone, reference_date=reference_date, time_format=time_format))
    else:
      return custom_transliteration.tr("%s~(%s##\\To{}##%s)" % (name, self.status_1_hk, self.status_2_hk), script=scripts[0])


class PushkaraFestivalInstance(FestivalInstance):
  """One of the 4 roles (Adya/antya x ArambhaH/samApanam) of a river's 12-year Pushkara residency.

  :param rashi_index: 1-indexed rashi (the *incoming* rashi for role='Adya', the *outgoing* one
    for role='antya') -- both the river and its names are looked up from this alone.
  """

  def __init__(self, rashi_index, role, stage, interval, general_note='', shlokas='', references='', url='',
               legend=''):
    from jyotisha.panchaanga.temporal import names
    from jyotisha.panchaanga.temporal.festival import pushkara_description
    river_hk = names.NAMES['PUSHKARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi_index]
    rashi_hk = names.NAMES['RASHI_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi_index]
    river_deva = names.NAMES['PUSHKARA_NAMES']['sa'][sanscript.DEVANAGARI][rashi_index]
    rashi_deva = names.NAMES['RASHI_NAMES']['sa'][sanscript.DEVANAGARI][rashi_index]
    name = '%s-%s-puSkara-%s' % (river_hk, role, stage)
    description = pushkara_description.describe_pushkara(
      role=role, stage=stage, rashi_sa=rashi_hk, river_sa=river_hk, general_note=general_note, shlokas=shlokas,
      references=references, url=url, legend=legend)
    role_sa = 'आद्य' if role == pushkara_description.ROLE_ADYA else 'अन्त्य'
    stage_sa = 'आरम्भः' if stage == pushkara_description.STAGE_ARAMBHAH else 'समापनम्'
    names_dict = {"sa": ["%s-%s-पुष्कर-%s" % (river_deva, role_sa, stage_sa)]}
    super().__init__(name=name, interval=interval, description=description, names=names_dict)


class EkadashiFestivalInstance(FestivalInstance):
  """The regular sarva-/smArta-/vaiSNava- Ekadashi of a given paksha+month.

  Named ekadashis added as bonus festivals alongside the regular one (vaikuNTha,
  guruvAyupura, kaizika, raMgabharI, ASADhI-vArI) are not built via this class --
  they keep going through the ordinary TOML lookup by their own exact fest_id.
  """

  def __init__(self, paksha, month_index, variant, interval, suffix=None, legend='', general_note='', shlokas='',
               references='', url=''):
    from jyotisha.panchaanga.temporal import names
    from jyotisha.panchaanga.temporal.festival import ekadashi_description
    ekad_base = names.get_ekaadashii_name(paksha, month_index)
    month_sa = names.get_chandra_masa(month=month_index, script=sanscript.roman.HK_DRAVIDIAN, visarga=False)
    name = '%s-%s%s' % (variant, ekad_base, (' %s' % suffix) if suffix else '')
    description = ekadashi_description.describe_ekadashi(
      ekad_base=ekad_base, paksha=paksha, month_sa=month_sa, legend=legend, general_note=general_note,
      shlokas=shlokas, references=references, url=url)
    super().__init__(name=name, interval=interval, description=description)


class AdhyayanaFestivalInstance(FestivalInstance):
  """An anadhyAya (no Vedic study) day whose description is one of a handful of shared
  boilerplate notes, layered with an optional per-instance label (see adhyayana_description.py).

  Unlike PushkaraFestivalInstance/EkadashiFestivalInstance, these are not constructed fresh
  by a dedicated method -- they start out as plain FestivalInstances built by the generic
  RuleLookupAssigner, and get upgraded to this class post-hoc once all festivals for the run
  are assigned (see TithiFestivalAssigner.upgrade_anadhyayana_festival_instances). `base_instance`
  supplies the name/interval/ordinal/exclude to carry over unchanged.
  """

  def __init__(self, base_instance, cluster, label, general_note='', shlokas='', blurb='', references='', url='',
               legend=''):
    from jyotisha.panchaanga.temporal.festival import adhyayana_description
    if label is not None:
      description = adhyayana_description.describe_labeled(
        label=label, general_note=general_note, shlokas=shlokas, blurb=blurb, references=references, url=url,
        legend=legend)
    else:
      description = adhyayana_description.describe_boilerplate(
        general_note=general_note, shlokas=shlokas, blurb=blurb, references=references, url=url)
    super().__init__(name=base_instance.name, interval=base_instance.interval, ordinal=base_instance.ordinal,
                      exclude=base_instance.exclude, description=description, names=base_instance.names)


def get_description(festival_instance, fest_details_dict, script, truncate=True, header_md="#####"):
  fest_id = festival_instance.name.replace('__', '_or_')
  if getattr(festival_instance, 'description', None) is not None:
    from jyotisha.panchaanga.temporal.festival.rules import summary
    desc_dict = festival_instance.description
    blurb = summary.transliterate_backticked_terms(desc_dict.get('blurb', ''))
    detailed = summary.transliterate_backticked_terms(desc_dict.get('detailed', ''))
    return "%s\n\n%s" % (blurb, detailed)
  desc = None
  if re.match('aGgArakI.*saGkaTahara-caturthI-vratam', fest_id):
    fest_id = fest_id.replace('aGgArakI~', '')
    if fest_id in fest_details_dict:
      desc = fest_details_dict[fest_id].get_description_string(
        script=script, header_md=header_md)
    else:
      logging.warning('No description found for caturthI festival %s!' % fest_id)
  elif 'amAvAsyA' in fest_id:
    desc = ''
    fest_id_orig = fest_id
    if 'alabhyam' in fest_id:
      alabhyam_tags = re.sub(r'.*alabhyam–(.*)\)', r'\1', fest_id_orig).split(',_')
      for tag in alabhyam_tags:
        if tag in ["ArdrA", "punarvasuH", "puSyaH", "svAtI", "vizAkhA", "anUrAdhA", "zraviSThA", "zatabhiSak", "pUrvaprOSThapadA"]:
          ama_fest = 'alabhya-nakSatra-amAvAsyA'
        else:
          ama_fest = '%s-amAvAsyA' % tag
        if ama_fest in fest_details_dict:
          desc += fest_details_dict[ama_fest].get_description_string(
            script=script, include_url=True, include_shlokas=True, truncate=truncate, header_md=header_md)
        else:
          logging.warning('No description found for **amAvAsyA festival %s!' % ama_fest)  
    if fest_id.startswith('sarva-'):
      fest_id = fest_id[len('sarva-'):]
      sarva = True
    elif fest_id.startswith('bOdhAyana-'):
      fest_id = fest_id[len('bOdhAyana-'):]
      bodhayana = True
    else:
      pass
    fest_id = re.sub('amAvAsyA.*', 'amAvAsyA', fest_id)
    if fest_id in fest_details_dict:
      desc = fest_details_dict[fest_id].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate, header_md=header_md) + desc
      logging.debug('Using description of %s for amAvAsyA festival %s!' % (fest_id, fest_id_orig))
    else:
      logging.warning('No description found for amAvAsyA festival %s!' % fest_id_orig)
  elif re.match('.*-.*-EkAdazI', fest_id) is not None:
    # Handle ekaadashii descriptions differently
    ekad = '-'.join(fest_id.split('-')[1:])  # get rid of sarva etc. prefix!
    ekad_suff_pos = ekad.find('_(')
    if ekad_suff_pos != -1:
      # ekad_suff = ekad[ekad_suff_pos + 1:-1]
      ekad = ekad[:ekad_suff_pos]
    if ekad in fest_details_dict:
      desc = fest_details_dict[ekad].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate, header_md=header_md)
    else:
      logging.warning('No description found for Ekadashi festival %s (%s)!' % (ekad, fest_id))
  elif fest_id.find('saGkrAntiH') != -1:
    # Handle Sankranti descriptions differently
    planet_trans = fest_id.split('~')[0]  # get rid of ~(rAshi name) etc.
    if planet_trans in fest_details_dict:
      desc = fest_details_dict[planet_trans].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate, header_md=header_md)
    else:
      logging.warning('No description found for festival %s!' % planet_trans)
  elif fest_id.find('saMvatsaraH') != -1:
    # Handle new year fest descriptions differently
    new_yr_fest = fest_id.split('~')[0]  # get rid of ~(rAshi name) etc.
    if new_yr_fest in fest_details_dict:
      desc = fest_details_dict[new_yr_fest].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate, header_md=header_md)
    else:
      logging.warning('No description found for festival %s!' % new_yr_fest)
  elif fest_id in fest_details_dict:
      desc = fest_details_dict[fest_id].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate, include_images=False, header_md=header_md)


  if desc is None:
      # Check approx. match
      matched_festivals = []
      if 'amAvAsyA' in fest_id: # Handle amAvAsyAs a bit differently
        if fest_id.startswith('sarva-'):
          fest_id = fest_id[len('sarva-'):]
      for fest_key in fest_details_dict:
        if fest_id in fest_key:
          if 'amAvAsyA' in fest_id: # Handle amAvAsyAs a bit differently
            if 'bOdhAyana' not in fest_id and 'bOdhAyana' in fest_key:
              continue
          matched_festivals += [fest_key]
      if matched_festivals == []:
        logging.warning('No description found for festival %s!' % fest_id)
      elif len(matched_festivals) > 1:
        logging.warning('No exact match found for festival %s! Found more than one approximate match: %s' % (
          fest_id, str(matched_festivals)))
      else:
        desc = fest_details_dict[matched_festivals[0]].get_description_string(script=script,
                                                                              include_url=True, include_shlokas=True,
                                                                              truncate=True, header_md=header_md)
  return default_if_none(desc, "")

def handle_chaturthi(fest_id, fest_details_dict, script, desc):
  for prefix in ['ravivAra-', 'aGgArakI~']:
    if fest_id.startswith(prefix):
      fest_id = fest_id.replace(prefix, '')
      if fest_id in fest_details_dict:
        desc = fest_details_dict[fest_id].get_description_dict(script=script)
        special_chaturthi_fest_desc = fest_details_dict[f'{prefix}caturthI'].get_description_dict(script=script)
        desc['detailed'] += ' ' + special_chaturthi_fest_desc['detailed']
        desc['references'] += special_chaturthi_fest_desc['references']
        desc['shlokas'] += special_chaturthi_fest_desc['shlokas']
        desc['url'] += ' ' + special_chaturthi_fest_desc['url']
      else:
        logging.warning('No description found for caturthI festival %s!' % fest_id)
  return desc

def handle_amavasya(fest_id, fest_details_dict, script, desc):
  fest_id_orig = fest_id
  if 'alabhyam' in fest_id:
    alabhyam_tags = re.sub(r'.*alabhyam–(.*)\)', r'\1', fest_id_orig).split(',_')
    for tag in alabhyam_tags:
      if tag in ["ArdrA", "punarvasuH", "puSyaH", "svAtI", "vizAkhA", "anUrAdhA", "zraviSThA", "zatabhiSak", "pUrvaprOSThapadA"]:
        ama_fest = 'alabhya-nakSatra-amAvAsyA'
      else:
        ama_fest = '%s-amAvAsyA' % tag
      if ama_fest in fest_details_dict:
        ama_fest_desc = fest_details_dict[ama_fest].get_description_dict(script=script)
        if desc:
          desc['detailed'] += " " + ama_fest_desc['detailed']
          desc['references'] += ama_fest_desc['references']
          desc['shlokas'] += ama_fest_desc['shlokas']
          desc['url'] += ' ' + ama_fest_desc['url']
        else:
          desc = ama_fest_desc
      else:
        logging.warning('No description found for **amAvAsyA festival %s!' % ama_fest)  
  if fest_id.startswith('sarva-'):
    fest_id = fest_id[len('sarva-'):]
    sarva = True
  elif fest_id.startswith('bOdhAyana-kAtyAyana-'):
    fest_id = fest_id[len('bOdhAyana-kAtyAyana-'):]
    bodhayana = True
  else:
    pass
  fest_id = re.sub('amAvAsyA.*', 'amAvAsyA', fest_id)
  if fest_id in fest_details_dict:
    ama_fest_desc = fest_details_dict[fest_id].get_description_dict(script=script)
    if desc:
      desc['detailed'] += " " + ama_fest_desc['detailed']
      desc['references'] += ama_fest_desc['references']
      desc['shlokas'] += ama_fest_desc['shlokas']
      desc['url'] += ' ' + ama_fest_desc['url']
    else:
      desc = ama_fest_desc
    # logging.debug('Using description of %s for amAvAsyA festival %s!' % (fest_id, fest_id_orig))
  else:
    logging.warning('No description found for amAvAsyA festival %s!' % fest_id_orig)
  return desc

def handle_ekadashi(fest_id, fest_details_dict, script, desc):
  # Handle ekaadashii descriptions differently
  ekad = '-'.join(fest_id.split('-')[1:])  # get rid of sarva etc. prefix!
  ekad_suff_pos = ekad.find('_(')
  if ekad_suff_pos != -1:
    # ekad_suff = ekad[ekad_suff_pos + 1:-1]
    ekad = ekad[:ekad_suff_pos]
  if ekad in fest_details_dict:
    desc = fest_details_dict[ekad].get_description_dict(script=script)
  else:
    logging.warning('No description found for Ekadashi festival %s (%s)!' % (ekad, fest_id))
  return desc

def handle_sankranti(fest_id, fest_details_dict, script, desc):
  # Handle Sankranti descriptions differently
  planet_trans = fest_id.split('~')[0]  # get rid of ~(rAshi name) etc.
  if planet_trans in fest_details_dict:
    desc = fest_details_dict[planet_trans].get_description_dict(script=script)
  else:
    logging.warning('No description found for festival %s!' % planet_trans)
  return desc

def handle_new_year(fest_id, fest_details_dict, script, desc):
  # Handle new year fest descriptions differently
  new_yr_fest = fest_id.split('~')[0]  # get rid of ~(rAshi name) etc.
  if new_yr_fest in fest_details_dict:
    desc = fest_details_dict[new_yr_fest].get_description_dict(script=script)
  else:
    logging.warning('No description found for festival %s!' % new_yr_fest)
  return desc

PATTERNS_TO_HANDLERS = {
  '.*saGkaTahara-caturthI-vratam': handle_chaturthi,
  '.*amAvAsyA.*': handle_amavasya,
  '.*-.*-EkAdazI': handle_ekadashi,
  '.*saGkrAntiH.*': handle_sankranti,
  '.*saMvatsaraH.*': handle_new_year,
}

def _get_description_dict(festival_instance, fest_details_dict, script):
  fest_id = festival_instance.name.replace('__', '_or_')
  if getattr(festival_instance, 'description', None) is not None:
    # Return a copy, not the stored reference: the same FestivalInstance can be rendered into
    # multiple scripts (e.g. multiple tex outputs sharing one computed Panchaanga), and both
    # backtick terms and shlokas are stored in their raw/canonical form (HK-Dravidian roman,
    # Devanagari respectively) precisely so each render can transliterate them correctly here
    # rather than baking one script in at construction time.
    from jyotisha.panchaanga.temporal.festival.rules import summary
    desc = dict(festival_instance.description)
    desc['blurb'] = summary.transliterate_backticked_terms(desc.get('blurb', ''))
    desc['detailed'] = summary.transliterate_backticked_terms(desc.get('detailed', ''))
    if desc.get('shlokas'):
      desc['shlokas'] = sanscript.transliterate(desc['shlokas'], sanscript.DEVANAGARI, script)
    return desc
  desc = {}

  for pattern, handler in PATTERNS_TO_HANDLERS.items():
    if re.match(pattern, fest_id):
      desc = handler(fest_id, fest_details_dict, script, desc)

  if fest_id in fest_details_dict:
    desc = fest_details_dict[fest_id].get_description_dict(script=script)

  if desc is None:
      # Check approx. match
      matched_festivals = []
      for fest_key in fest_details_dict:
        if fest_id.startswith(fest_key):
          matched_festivals += [fest_key]
      if matched_festivals == []:
        logging.warning('No description found for festival %s!' % fest_id)
      elif len(matched_festivals) > 1:
        logging.warning('No exact match found for festival %s! Found more than one approximate match: %s' % (
          fest_id, str(matched_festivals)))
      else:
        desc = fest_details_dict[matched_festivals[0]].get_description_dict(script=script)

  return desc

def _texify_description_dict(desc, fest_id):
  if desc == {}:
    logging.warning('No description found for %s' % fest_id)
    return '{}{}{}{}{} %%EMPTY DESCRIPTION!'
  else:
    desc['detailed'] = desc['detailed'].replace('&', '\\&').replace('\n', '\\\\').replace('\\\\\\\\', '\\\\').replace('## ', '')
    desc['detailed'] = desc['detailed'][:1].capitalize() + desc['detailed'][1:]
    desc['shlokas'] = desc['shlokas'].strip('\n').replace('\n', '\\\\').replace('\\\\\\\\', '\\\\').replace('\\\\  \\\\', '\\\\\\smallskip ').replace('[','{}%\n[')
    desc['references'] = desc['references'].replace('- References\n  ', '')
    return '{%s}\n{%s}\n{%s}\n{%s}\n{%s}\n{%s}' % (desc['blurb'].replace('_', '\\_').replace('##~##','~'), 
                                     desc['detailed'].replace('_', '\\_'),
                                     desc['image'], desc['shlokas'],
                                     desc['references'].replace('_', '\\_'),
                                     '|'.join(['\\href{%s}{\\scriptsize EDIT...}' % url.replace('%', '\\%') for url in desc['url'].split(' ')]),
                                     )
  
def get_description_tex(festival_instance, fest_details_dict, script):
  # Returns '{blurb}{detailed-description}{image}{shlokas}{references}'
  fest_id = festival_instance.name.replace('__', '_or_')
  desc = _get_description_dict(festival_instance, fest_details_dict, script)
  return _texify_description_dict(desc, fest_id)

def get_combined_description_tex(festival_instance_list, fest_details_dict, script):
  def _removeDuplicates(listofElements):
    spacers = ['']
    uniqueList = []
    for elem in listofElements:
        if elem not in uniqueList or elem in spacers:
            uniqueList.append(elem)

    return uniqueList

  combined_desc = {'shlokas': '', 'url': '', 'blurb': '', 'image': '', 'references': '', 'detailed': ''}
  combined_desc_list = []
  for festival_instance in festival_instance_list:
    desc = _get_description_dict(festival_instance, fest_details_dict, script)
    if len(desc):
      combined_desc_list.append(desc)

  combined_desc['detailed'] = ' '.join([desc['detailed'] for desc in combined_desc_list])
  combined_desc['shlokas'] = '\n'.join(_removeDuplicates(('\n'.join([desc['shlokas'] for desc in combined_desc_list]).split('\n'))))
  combined_desc['references'] = '\n'.join([desc['references'] for desc in combined_desc_list])
  combined_desc['url'] = ' '.join([desc['url'] for desc in combined_desc_list])
  combined_desc['blurb'] = (' '.join([desc['blurb'] for desc in combined_desc_list])).strip()
  combined_desc['image'] = (' '.join([desc['image'] for desc in combined_desc_list])).strip()

  return _texify_description_dict(combined_desc, 'anadhyAyaH')


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
