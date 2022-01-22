import swisseph as swe

# These are present in http://www.astro.com/swisseph/swephprg.htm#_Toc471829094 but not in the swe python module.
import jyotisha
from indic_transliteration import sanscript
from jyotisha.custom_transliteration import tr
from jyotisha.panchaanga.temporal.names.init_names_auto import init_names_auto


def get_ayanaamsha_name(ayanaamsha_id):
  return swe.get_ayanamsa_name(ayanaamsha_id)


def get_ekaadashii_name(paksha, lmonth):
  """Return the name of an ekaadashii
  """
  if paksha == "shukla":
    if lmonth == int(lmonth):
      return "%s-EkAdazI" % NAMES["SHUKLA_EKADASHI_NAMES"]["sa"][sanscript.roman.HK_DRAVIDIAN][lmonth]
    else:
      # adhika mAsam
      return "%s-EkAdazI" % NAMES["SHUKLA_EKADASHI_NAMES"]["sa"][sanscript.roman.HK_DRAVIDIAN][13]
  elif paksha == "krishna":
    if lmonth == int(lmonth):
      return "%s-EkAdazI" % NAMES["KRISHNA_EKADASHI_NAMES"]["sa"][sanscript.roman.HK_DRAVIDIAN][lmonth]
    else:
      # adhika mAsam
      return "%s-EkAdazI" % NAMES["KRISHNA_EKADASHI_NAMES"]["sa"][sanscript.roman.HK_DRAVIDIAN][13]


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


def get_month_name_en(month_number, month_type, script=sanscript.ISO):
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
  "raatri_gulika": "रात्रौ गुलिककालः",
  "yama": "यमघण्टः",
  "raatri_yama": "रात्रौ यमघण्टः",
  "raatri_yaama": "रात्रौ यामाः",
  "raatri_yaama_1": "रात्रौ यामः १",
  "raatri_yaama_2": "रात्रौ यामः २",
  "raatri_yaama_3": "रात्रौ यामः ३",
  "raatri_yaama_4": "रात्रौ यामः ४",
  "ahar_yaama": "अह्नि यामाः",
  "ahar_yaama_1": "अह्नि यामः १",
  "ahar_yaama_2": "अह्नि यामः २",
  "ahar_yaama_3": "अह्नि यामः ३",
  "ahar_yaama_4": "अह्नि यामः ४",
  "shraadhaarambha_mukhya": "श्राद्धारम्भ-कालः (मुख्यः)",
  "shraadhaarambha_gauna": "श्राद्धारम्भ-कालः (गौणः)",
  "shraadha_kaala": "श्राद्ध-कालः",
  "shayana": "शयनकालः",
  "dinaanta": "दिनान्तम्",
  "preceding_arunodaya": "प्राक्तनारुणोदयः",
  "maadhyaahnika_sandhyaa": "माध्याह्निकसन्ध्यावन्दनकालः",
  "puurvaahna": "पूर्वाह्णः",
  "raatrimaana": "रात्रिमानम्",
  "dinamaana": "दिनमानम्",
  "sunrise": "सूर्योदयः",
  "sunset": "सूर्यास्तमयः",
  "moonrise": "चन्द्रोदयः",
  "raudra" : "रौद्रः",
  "chaitra" : "चैत्रः",
  "maitra" : "मैत्रः",
  "saalakata" : "सालकटः",
  "saavitra" : "सावित्रः",
  "jayanta" : "जयन्तः",
  "gaandharva" : "गान्धर्वः",
  "kutapa" : "कुतपः",
  "rauhina" : "रौहिणः",
  "virinchi" : "विरिञ्चिः",
  "vijaya" : "विजयः",
  "nairrita" : "नैर्‌ऋतः",
  "mahendra" : "महेन्द्रः",
  "varuna" : "वरुणः",
  "bodha" : "बोधः",
  "shankara" : "शङ्करः",
  "ajapaat" : "अजपात्",
  "ahirbudhnya" : "अहिर्बुध्न्यः",
  "puushaka" : "पूषकः",
  "aashvina" : "आश्विनः",
  "yaamyava" : "याम्यः",
  "aahneya" : "आह्नेयः",
  "vaidhaatra" : "वैधात्रः",
  "chaandra" : "चान्द्रः",
  "aaditeya" : "आदितेयः",
  "jaiva" : "जैवः",
  "vaishnava" : "वैष्णवः",
  "saura" : "सौरः",
  "succeeding_braahma" : "ब्राह्मः",
  "naabhasvata" : "नाभस्वतः",  
  "durmuhurta1" : "दुर्मुहूर्तः १",  
  "durmuhurta2" : "दुर्मुहूर्तः २",  
} 

devanaagarii_to_python = {python_to_devanaagarii[x]: x for x in python_to_devanaagarii }

sa_to_tamil = dict(**NAMES["SA_TO_TAMIL"], **{sanscript.transliterate(x, sanscript.DEVANAGARI, sanscript.roman.HK_DRAVIDIAN):NAMES["SA_TO_TAMIL"][x] for x  in NAMES["SA_TO_TAMIL"]})


def translate_or_transliterate(text, script, source_script=sanscript.roman.HK_DRAVIDIAN):
  if script == "tamil":
    if text in sa_to_tamil:
      return sa_to_tamil[text]
    else:
      return jyotisha.custom_transliteration.tr(text, script, source_script=source_script)
  else:
    return jyotisha.custom_transliteration.tr(text, script, source_script=source_script)

def get_tipu_month_str(month):
  """
  
  Reference: https://toshkhana.wordpress.com/2014/09/19/dawn-of-a-new-era-tipu-sultan-and-his-mauludi-calendar/
  :param month: 
  :return: 
  """
  if month == int(month):
    month_str = " / ".join([NAMES["TIPU_ABJAD_MONTH_NAMES"]["fa"][int(month) - 1], NAMES["TIPU_ABTATH_MONTH_NAMES"]["fa"][int(month) - 1]])
    return month_str
  else:
    month_str = " / ".join([NAMES["TIPU_ABJAD_MONTH_NAMES"]["fa"][int(month)], NAMES["TIPU_ABTATH_MONTH_NAMES"]["fa"][int(month)]])
    return "%s (adhika)" % (month_str)
