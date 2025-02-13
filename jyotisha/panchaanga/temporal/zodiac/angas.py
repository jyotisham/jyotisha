import math
from numbers import Number

import methodtools
from jyotisha.panchaanga.temporal import names, Graha

from sanskrit_data.schema import common
from indic_transliteration import sanscript

NAME_TO_TYPE = {}


class AngaType(common.JsonObject):
  # The below class variables are declared here, but instantiated later.
  TITHI = None
  TITHI_PADA = None
  NAKSHATRA = None
  NAKSHATRA_PADA = None
  RASHI = None
  YOGA = None
  KARANA = None
  TROPICAL_MONTH = None
  SOLAR_NAKSH = None
  SOLAR_NAKSH_PADA = None
  SAMVATSARA = None
  GRAHA_RASHI = {}

  def __init__(self, name, name_hk, num_angas, body_weights=None, mean_period_days=None, names_dict=None):
    if body_weights is None:
      body_weights = {}
    super(AngaType, self).__init__()
    self.name = name
    self.name_hk = name_hk
    self.num_angas = num_angas
    self.arc_length = 360.0 / num_angas
    self.body_weights = body_weights
    self.mean_period_days = mean_period_days
    if names_dict is None:
      if name == 'SOLAR_NAKSH':
        key = 'NAKSHATRA_NAMES'
      elif name == 'SIDEREAL_MONTH':
        key = 'CHANDRA_MASA_NAMES'
      elif name.startswith("RASHI"):
        key = 'RASHI_NAMES'
      else:
        key = name + "_NAMES"
      if key in names.NAMES:
        self.names_dict = names.NAMES[key]['sa']
    else:
      self.names_dict = names_dict
    NAME_TO_TYPE[self.name] = self

  def get_body_str(self):
    body_str = ""
    for body in self.body_weights:
      body_str = f"{body} {body_str}"
    return body_str.strip()

  def add(self, a, b):
    if b < 1:
      offset_index = (a + b) % self.num_angas
    else:
      offset_index = (a - 1 + b) % self.num_angas + 1
    return offset_index

  def __hash__(self):
    return hash(self.name)

  def __repr__(self):
    return self.name

  def __eq__(self, other):
    # Overriding for speed.
    return self.name == other.name

  @classmethod
  def from_name(cls, name):
    return NAME_TO_TYPE[name.upper()]



AngaType.TITHI = AngaType(name='TITHI', name_hk="tithiH", num_angas=30, body_weights={Graha.MOON: 1, Graha.SUN: -1}, mean_period_days=29.530588)
AngaType.TITHI_PADA = AngaType(name='TITHI_PADA', name_hk="tithi-pAdaH", num_angas=120, body_weights={Graha.MOON: 1, Graha.SUN: -1}, mean_period_days=29.530588)
AngaType.NAKSHATRA = AngaType(name='NAKSHATRA', name_hk="nakSatram", num_angas=27, body_weights={Graha.MOON: 1, Graha.SUN: 0}, mean_period_days=27.321661)
AngaType.NAKSHATRA_PADA = AngaType(name='NAKSHATRA_PADA', name_hk="nakSatra-pAdaH", num_angas=108, body_weights={Graha.MOON: 1, Graha.SUN: 0}, mean_period_days=27.321661)
AngaType.RASHI = AngaType(name='RASHI', name_hk="rAziH", num_angas=12, body_weights={Graha.MOON: 1, Graha.SUN: 0}, mean_period_days=27.321661)
AngaType.YOGA = AngaType(name='YOGA', name_hk="yOgaH", num_angas=27, body_weights={Graha.MOON: 1, Graha.SUN: 1}, mean_period_days=29.541)
AngaType.YOGA_PADA = AngaType(name='YOGA_PADA', name_hk="yOga-pAdaH", num_angas=108, body_weights={Graha.MOON: 1, Graha.SUN: 1}, mean_period_days=29.541)
AngaType.KARANA = AngaType(name='KARANA', name_hk="karaNam", num_angas=60, body_weights={Graha.MOON: 1, Graha.SUN: -1}, mean_period_days=29.4)
AngaType.TROPICAL_MONTH = AngaType(name='TROPICAL_MONTH', name_hk="Artava-mAsaH", num_angas=12, body_weights={Graha.MOON: 0, Graha.SUN: 1}, mean_period_days=365.242)
AngaType.SOLAR_NAKSH = AngaType(name='SOLAR_NAKSH', name_hk="saura-nakSatram", num_angas=27, body_weights={Graha.MOON: 0, Graha.SUN: 1}, mean_period_days=365.242)
AngaType.SOLAR_NAKSH_PADA = AngaType(name='SOLAR_NAKSH_PADA', name_hk="saura-nakSatra-pAdaH", num_angas=108, body_weights={Graha.MOON: 0, Graha.SUN: 1}, mean_period_days=365.242)
AngaType.SAMVATSARA = AngaType(name='SAMVATSARA', name_hk="saMvatsaraH", num_angas=64, mean_period_days=None)

AngaType.GRAHA_RASHI[Graha.SUN] = AngaType(name='RASHI_SUN', name_hk="sUrya-rAziH", num_angas=12, body_weights={Graha.SUN: 1}, mean_period_days=365.242)
AngaType.GRAHA_RASHI[Graha.MERCURY] = AngaType(name='RASHI_MERCURY', name_hk="budha-rAziH", num_angas=12, body_weights={Graha.MERCURY: 1}, mean_period_days=87.97)
AngaType.GRAHA_RASHI[Graha.VENUS] = AngaType(name='RASHI_VENUS', name_hk="zukra-rAziH", num_angas=12, body_weights={Graha.VENUS: 1}, mean_period_days=224.7)
AngaType.GRAHA_RASHI[Graha.MARS] = AngaType(name='RASHI_MARS', name_hk="maGgala-rAziH", num_angas=12, body_weights={Graha.MARS: 1}, mean_period_days=686.98)
AngaType.GRAHA_RASHI[Graha.JUPITER] = AngaType(name='RASHI_JUPITER', name_hk="guru-rAziH", num_angas=12, body_weights={Graha.JUPITER: 1}, mean_period_days=4333)
AngaType.GRAHA_RASHI[Graha.SATURN] = AngaType(name='RASHI_SATURN', name_hk="zani-rAziH", num_angas=12, body_weights={Graha.SATURN: 1}, mean_period_days=10756)
AngaType.GRAHA_RASHI[Graha.RAHU] = AngaType(name='RASHI_RAHU', name_hk="rAhu-rAziH", num_angas=12, body_weights={Graha.RAHU: 1}, mean_period_days=6798.383)
AngaType.GRAHA_RASHI[Graha.KETU] = AngaType(name='RASHI_KETU', name_hk="kEtu-rAziH", num_angas=12, body_weights={Graha.KETU: 1}, mean_period_days=6798.383)

class Anga(common.JsonObject):
  """
  Crucial assumption about an anga is that it'r range starts with 1, and not 0.
  
  """
  def __init__(self, index, anga_type_id):
    super(Anga, self).__init__()
    self.index = index
    self.anga_type_id = anga_type_id

  @methodtools.lru_cache()
  @classmethod
  def get_cached(self, index, anga_type_id):
    return Anga(index=index, anga_type_id=anga_type_id)

  def get_name(self, script=sanscript.roman.HK_DRAVIDIAN):
    name_dict = NAME_TO_TYPE[self.anga_type_id].names_dict
    if name_dict is not None:
      return name_dict[script][self.index]
    else:
      return None

  def get_type(self):
    return NAME_TO_TYPE[self.anga_type_id]

  def __repr__(self):
    return "%s: %02.1f" % (self.anga_type_id, self.index)

  def __sub__(self, other):
    """ 
    
    Consider the 27 nakshatras. 
    Expectations: 
      - nakshatra 1 - nakshatra 27 = 1 (not -26).
      - nakshatra 27 - nakshatra 1 = -1 (not 26).
    
    :return: 
    """
    if isinstance(other, Number):
      # We're offsetting angas.
      offset_index = (self.index - other - 1) % self.get_type().num_angas + 1
      return Anga.get_cached(index=offset_index, anga_type_id=self.anga_type_id)
    else:
      # In this case, we're measuring gap between angas.
      # Below is skipped for efficiency.
      # if self.anga_type_id != other.anga_type_id: raise ValueError("anga_type mismatch!", (self.anga_type_id, other.anga_type_id))
      num_angas = NAME_TO_TYPE[self.anga_type_id].num_angas
      gap = min((self.index - other.index) % num_angas, (other.index - self.index) % num_angas)
      if math.isclose((self.index - 1 + gap) % num_angas, other.index - 1):
        return -gap
      else:
        return gap

  def __mod__(self, other):
    # We avoid if isinstance(other, Number) for efficiency.
    # We don't construct an anga object to avoid confusion between shukla and kRShNa paxa tithis. 
    return self.index % other

  def __add__(self, other):
    # Addition is only for offsetting an anga.
    # We avoid if isinstance(other, Number) for efficiency.
    if other < 1:
      offset_index = (self.index + other) % NAME_TO_TYPE[self.anga_type_id].num_angas
    else:
      offset_index = (self.index - 1 + other) % NAME_TO_TYPE[self.anga_type_id].num_angas + 1
    return Anga.get_cached(index=offset_index, anga_type_id=self.anga_type_id)

  def __lt__(self, other):
   return self - other < 0

  def __gt__(self, other):
    return self - other > 0

  def __ge__(self, other):
    return self > other or self == other

  def __le__(self, other):
    return self < other or self == other

  def __eq__(self, other):
    return self.index == other.index

  def __hash__(self):
    return super(Anga, self).__hash__()


class Tithi(Anga):
  def __init__(self, index, month):
    super(Tithi, self).__init__(index=index, anga_type_id=AngaType.TITHI.name)
    self.month = month

  @classmethod
  def from_anga(cls, anga, month):
    return Tithi(index=anga.index, month=month)

  def __repr__(self):
    if self.month is not None:
      return f"{self.anga_type_id}: {self.month.index:4.1f}:{self.index:02d}"
    else:
      return f"{self.anga_type_id}: ??:{self.index:02d}"


class BoundaryAngas(common.JsonObject):
  def __init__(self, start, end, interval=None):
    super(BoundaryAngas, self).__init__()
    self.start = start
    self.end = end
    self.interval = interval

  def to_tuple(self):
    return (None if self.start is None else self.start.index, None if self.end is None else self.end.index)

  def __repr__(self):
    return "%s-%s %s" % (str(self.start), str(self.end), str(self.interval))