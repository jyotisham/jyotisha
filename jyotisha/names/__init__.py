import swisseph as swe

# These are present in http://www.astro.com/swisseph/swephprg.htm#_Toc471829094 but not in the swe python module.
import jyotisha
from jyotisha.custom_transliteration import tr
from jyotisha.names.init_names_auto import init_names_auto

SIDM_TRUE_PUSHYA = 29
SIDM_TRUE_MULA = 35

month_map = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
       5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September',
       10: 'October', 11: 'November', 12: 'December'}
weekday_short_map = {0: 'Sun', 1: 'Mon', 2: 'Tue',
        3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}
weekday_map = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
SHULAM = [('pratIcI dik', 12, 'guDam'), ('prAcI dik', 8, 'dadhi'), ('udIcI dik', 12, 'kSIram'),
          ('udIcI dik', 16, 'kSIram'), ('dakSiNA dik', 20, 'tailam'), ('pratIcI dik', 12, 'guDam'),
          ('prAcI dik', 8, 'dadhi')]


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


def get_chandra_masa(month, script, visarga=True):
  if visarga:
    if month == int(month):
      return NAMES['CHANDRA_MASA_NAMES'][script][int(month)]
    else:
      return '%s-(%s)' % (NAMES['CHANDRA_MASA_NAMES'][script][int(month) + 1], tr('adhikaH', script, titled=False))
  else:
    if month == int(month):
      return NAMES['CHANDRA_MASA_NAMES'][script][int(month)][:-1]
    else:
      return '%s-(%s)' % (NAMES['CHANDRA_MASA_NAMES'][script][int(month) + 1][:-1], tr('adhika', script, titled=False))


NAMES = init_names_auto()


def translate_and_transliterate(text, language):
  translation = {'candrAstamayaH': 'சந்த்ராஸ்தமனம்',
                 'kSEtram': 'குறிப்பிட்ட ஊருக்கான தகவல்கள்',
                 'candrOdayaH': 'சந்த்ரோதயம்',
                 'cAndramAnam': 'சாந்த்ரமானம்',
                 'ahOrAtram': 'நாள் முழுவதும்',
                 'tithiH': 'திதி',
                 'dinaM': 'தேதி',
                 'pakSaH': 'பக்ஷம்',
                 'nakSatram': 'நக்ஷத்ரம்',
                 'yOgaH': 'யோகம்',
                 'mAsaH': 'மாஸம்',
                 'RtuH': 'ருதுஃ',
                 'ayanam': 'அயனம்',
                 'karaNam': 'கரணம்',
                 'rAziH': 'ராஶிஃ',
                 'lagnam': 'லக்னம்',
                 'candrASTama-rAziH': 'சந்த்ராஷ்டம-ராஶிஃ',
                 'zUlam': 'ஶூலம்',
                 'vAsaraH': 'வாஸரம்',
                 'dina-vizESAH': 'தின-விஶேஷங்கள்',
                 'saMvatsaraH': 'ஸம்வத்ஸரம்',
                 'sUryAstamayaH': 'ஸூர்யாஸ்தமனம்',
                 'sUryOdayaH': 'ஸூர்யோதயம்',
                 'sauramAnam': 'ஸௌரமானம்',
                 'dinAntaH': 'தினாந்தம்',
                 'aparAhNa-kAlaH': 'அபராஹ்ண-காலம்',
                 'rAhukAlaH': 'ராஹுகாலம்',
                 'yamaghaNTaH': 'யமகண்டம்',
                 'gulikakAlaH': 'குலிககாலம்',
                 'parihAraH': 'பரிஹாரம்',
                 'guDam': 'வெல்லம்',
                 'dadhi': 'தயிர்',
                 'kSIram': 'பால்',
                 'tailam': 'எண்ணெய்',
                 'prAcI dik': 'கிழக்கு',
                 'udIcI dik': 'வடக்கு',
                 'dakSiNA dik': 'தெற்கு ',
                 'pratIcI dik': 'மேற்கு'
                 }
  if language == 'tamil':
    if text in translation:
      return translation[text]
    else:
      return jyotisha.custom_transliteration.tr(text, language)
  else:
    return jyotisha.custom_transliteration.tr(text, language)