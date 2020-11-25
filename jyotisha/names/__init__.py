import swisseph as swe

# These are present in http://www.astro.com/swisseph/swephprg.htm#_Toc471829094 but not in the swe python module.
from jyotisha.custom_transliteration import tr
from jyotisha.names.init_names_auto import init_names_auto

SIDM_TRUE_PUSHYA = 29
SIDM_TRUE_MULA = 35


def get_ayanaamsha_name(ayanaamsha_id):
  if ayanaamsha_id == SIDM_TRUE_MULA:
    return "true mula"
  if ayanaamsha_id == SIDM_TRUE_PUSHYA:
    return "true pushya"
  return swe.get_ayanamsa_name(ayanaamsha_id)


def get_ekaadashii_name(paksha, lmonth):
  """Return the name of an ekaadashii
  """
  if paksha == 'shukla':
    if lmonth == int(lmonth):
      return '%s-EkAdazI' % NAMES['SHUKLA_EKADASHI_NAMES']['hk'][lmonth]
    else:
      # adhika mAsam
      return '%s-EkAdazI' % NAMES['SHUKLA_EKADASHI_NAMES']['hk'][13]
  elif paksha == 'krishna':
    if lmonth == int(lmonth):
      return '%s-EkAdazI' % NAMES['KRISHNA_EKADASHI_NAMES']['hk'][lmonth]
    else:
      # adhika mAsam
      return '%s-EkAdazI' % NAMES['KRISHNA_EKADASHI_NAMES']['hk'][13]


def get_chandra_masa(month, NAMES, script, visarga=True):
  if visarga:
    if month == int(month):
      return NAMES['CHANDRA_MASA_NAMES'][script][month]
    else:
      return '%s-(%s)' % (NAMES['CHANDRA_MASA_NAMES'][script][int(month) + 1], tr('adhikaH', script, titled=False))
  else:
    if month == int(month):
      return NAMES['CHANDRA_MASA_NAMES'][script][int(month)][:-1]
    else:
      return '%s-(%s)' % (NAMES['CHANDRA_MASA_NAMES'][script][int(month) + 1][:-1], tr('adhika', script, titled=False))


NAMES = init_names_auto()
