import swisseph as swe

# These are present in http://www.astro.com/swisseph/swephprg.htm#_Toc471829094 but not in the swe python module.
import jyotisha
from indic_transliteration import xsanscript
from jyotisha.custom_transliteration import tr
from jyotisha.panchaanga.temporal.names.init_names_auto import init_names_auto

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
  if paksha == "shukla":
    if lmonth == int(lmonth):
      return "%s-EkAdazI" % NAMES["SHUKLA_EKADASHI_NAMES"]["sa"]["hk"][lmonth]
    else:
      # adhika mAsam
      return "%s-EkAdazI" % NAMES["SHUKLA_EKADASHI_NAMES"]["sa"]["hk"][13]
  elif paksha == "krishna":
    if lmonth == int(lmonth):
      return "%s-EkAdazI" % NAMES["KRISHNA_EKADASHI_NAMES"]["sa"]["hk"][lmonth]
    else:
      # adhika mAsam
      return "%s-EkAdazI" % NAMES["KRISHNA_EKADASHI_NAMES"]["sa"]["hk"][13]


def get_chandra_masa(month, script, visarga=True):
  if visarga:
    if month == int(month):
      return NAMES["CHANDRA_MASA_NAMES"]["sa"][script][int(month)]
    else:
      return "%s-(%s)" % (NAMES["CHANDRA_MASA_NAMES"]["sa"][script][int(month) + 1], tr("adhikaH", script, titled=False))
  else:
    if month == int(month):
      return NAMES["CHANDRA_MASA_NAMES"]["sa"][script][int(month)][:-1]
    else:
      return "%s-(%s)" % (NAMES["CHANDRA_MASA_NAMES"]["sa"][script][int(month) + 1][:-1], tr("adhika", script, titled=False))


NAMES = init_names_auto()
month_map = {1: "January", 2: "February", 3: "March", 4: "April",
             5: "May", 6: "June", 7: "July", 8: "August", 9: "September",
             10: "October", 11: "November", 12: "December"}
weekday_short_map = {0: "Sun", 1: "Mon", 2: "Tue",
                     3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
weekday_map = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
SHULAM = NAMES["SHUULAM"]["sa"]

sa_to_tamil = dict(**NAMES["SA_TO_TAMIL"], **{xsanscript.transliterate(x, xsanscript.DEVANAGARI, xsanscript.HK):NAMES["SA_TO_TAMIL"][x] for x  in NAMES["SA_TO_TAMIL"]})


def translate_or_transliterate(text, script, source_script=xsanscript.HK):
  if script == "tamil":
    if text in sa_to_tamil:
      return sa_to_tamil[text]
    else:
      return jyotisha.custom_transliteration.tr(text, script, source_script=source_script)
  else:
    return jyotisha.custom_transliteration.tr(text, script, source_script=source_script)