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


def get_month_name_en(month_number, month_type, script=xsanscript.IAST):
  from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
  if month_number == 0:
    return "every"
  if month_type == RulesRepo.LUNAR_MONTH_DIR:
    return get_chandra_masa(month_number, script)
  elif month_type == RulesRepo.SIDEREAL_SOLAR_MONTH_DIR:
    return NAMES['RASHI_NAMES']['sa'][script][month_number]
  elif month_type == RulesRepo.TROPICAL_MONTH_DIR:
    return NAMES['RTU_MASA_NAMES_SHORT']['sa'][script][month_number]
  elif month_type == RulesRepo.GREGORIAN_MONTH_DIR:
    return month_map[month_number]


def get_samvatsara_name(offset_from_1987, samvatsara_index_1987=1):
  from jyotisha.panchaanga.temporal import Anga
  from jyotisha.panchaanga.temporal import AngaType
  samvatsara = offset_from_1987 + Anga(index=samvatsara_index_1987, anga_type_id=AngaType.SAMVATSARA)
  return samvatsara.get_name()


NAMES = init_names_auto()
month_map = {1: "January", 2: "February", 3: "March", 4: "April",
             5: "May", 6: "June", 7: "July", 8: "August", 9: "September",
             10: "October", 11: "November", 12: "December"}
weekday_short_map = {0: "Sun", 1: "Mon", 2: "Tue",
                     3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
weekday_map = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
SHULAM = NAMES["SHUULAM"]["sa"]
python_to_devanaagarii = {
  "braahma": "ब्राह्मं मुहूर्तम्",
  "praatah": "प्रातः",
  "aparaahna": "अपराह्णः",
  "saangava": "साङ्गवः",
  "madhyaahna": "मध्याह्नः",
  "saayaahna": "सायाह्नः",
  "pradosha": "प्रदोषः",
  "saayam_sandhyaa": "सायंसन्ध्यावन्दनकालः",
  "praatas_sandhyaa": "प्रातःसन्ध्यावन्दनकालः",
  "madhyaraatri": "मध्यरात्रिः",
  "nishiitha": "निशीथः",
  "raahu": "राहुकालः",
  "gulika": "गुलिककालः",
  "yama": "यमघण्टः",
  "raatri_yaama_1": "यामः प्रथमः",
  "shayana": "शयनकालः",
  "dinaanta": "दिनान्तम्",
  "preceeding_arunodaya": "प्राक्तनारुणोदयः",
  "maadhyaahnika_sandhyaa": "माध्याह्निकसन्ध्यावन्दनकालः",
  "puurvaahna": "पूर्वाह्णः",
  "raatrimaana": "रात्रिमानम्",
  "dinamaana": "दिनमानम्",
  "sunrise": "सूर्योदयः",
  "sunset": "सूर्यास्तमयः",
  "moonrise": "चन्द्रोदयः",
} 

devanaagarii_to_python = {python_to_devanaagarii[x]: x for x in python_to_devanaagarii }

sa_to_tamil = dict(**NAMES["SA_TO_TAMIL"], **{xsanscript.transliterate(x, xsanscript.DEVANAGARI, xsanscript.HK):NAMES["SA_TO_TAMIL"][x] for x  in NAMES["SA_TO_TAMIL"]})


def translate_or_transliterate(text, script, source_script=xsanscript.HK):
  if script == "tamil":
    if text in sa_to_tamil:
      return sa_to_tamil[text]
    else:
      return jyotisha.custom_transliteration.tr(text, script, source_script=source_script)
  else:
    return jyotisha.custom_transliteration.tr(text, script, source_script=source_script)