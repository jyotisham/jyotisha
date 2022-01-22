import math
from numbers import Number

import methodtools
from jyotisha.panchaanga.temporal import names

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
  SIDEREAL_MONTH = None
  TROPICAL_MONTH = None
  SOLAR_NAKSH = None
  SOLAR_NAKSH_PADA = None
  SAMVATSARA = None

  def __init__(self, name, name_hk, num_angas, weight_moon, weight_sun, mean_period_days=None, names_dict=None):
    super(AngaType, self).__init__()
    self.name = name
    self.name_hk = name_hk
    self.num_angas = num_angas
    self.arc_length = 360.0 / num_angas
    self.weight_moon = weight_moon
    self.weight_sun = weight_sun
    self.mean_period_days = mean_period_days
    if names_dict is None:
      if name == 'SOLAR_NAKSH':
        key = 'NAKSHATRA_NAMES'
      elif name == 'SIDEREAL_MONTH':
        key = 'CHANDRA_MASA_NAMES'
      else:
        key = name + "_NAMES"
      if key in names.NAMES:
        self.names_dict = names.NAMES[key]['sa']
    NAME_TO_TYPE[self.name] = self

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



AngaType.TITHI = AngaType(name='TITHI', name_hk="tithiH", num_angas=30, weight_moon=1, weight_sun=-1, mean_period_days=29.530588)
AngaType.TITHI_PADA = AngaType(name='TITHI_PADA', name_hk="tithi-pAdaH", num_angas=120, weight_moon=1, weight_sun=-1, mean_period_days=29.530588)
AngaType.NAKSHATRA = AngaType(name='NAKSHATRA', name_hk="nakSatram", num_angas=27, weight_moon=1, weight_sun=0, mean_period_days=27.321661)
AngaType.NAKSHATRA_PADA = AngaType(name='NAKSHATRA_PADA', name_hk="nakSatra-pAdaH", num_angas=108, weight_moon=1, weight_sun=0, mean_period_days=27.321661)
AngaType.RASHI = AngaType(name='RASHI', name_hk="rAshiH", num_angas=12, weight_moon=1, weight_sun=0, mean_period_days=27.321661)
AngaType.YOGA = AngaType(name='YOGA', name_hk="yOgaH", num_angas=27, weight_moon=1, weight_sun=1, mean_period_days=29.541)
AngaType.KARANA = AngaType(name='KARANA', name_hk="karaNam", num_angas=60, weight_moon=1, weight_sun=-1, mean_period_days=29.4)
AngaType.DEGREE = AngaType(name='DEGREE', name_hk=None, num_angas=360, weight_moon=None, weight_sun=None)
AngaType.SIDEREAL_MONTH = AngaType(name='SIDEREAL_MONTH', name_hk="rAzi-mAsaH", num_angas=12, weight_moon=0, weight_sun=1, mean_period_days=365.242)
AngaType.TROPICAL_MONTH = AngaType(name='TROPICAL_MONTH', name_hk="Artava-mAsaH", num_angas=12, weight_moon=0, weight_sun=1, mean_period_days=365.242)
AngaType.SOLAR_NAKSH = AngaType(name='SOLAR_NAKSH', name_hk="saura-nakSatram", num_angas=27, weight_moon=0, weight_sun=1, mean_period_days=365.242)
AngaType.SOLAR_NAKSH_PADA = AngaType(name='SOLAR_NAKSH_PADA', name_hk="saura-nakSatra-pAdaH", num_angas=108, weight_moon=0, weight_sun=1, mean_period_days=365.242)
AngaType.SAMVATSARA = AngaType(name='SAMVATSARA', name_hk="saMvatsaraH", num_angas=64, weight_moon=None, weight_sun=None, mean_period_days=None)


class Anga(common.JsonObject):
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
    if self.anga_type_id == AngaType.SIDEREAL_MONTH.name:
      return names.get_chandra_masa(month=self.index, script=script)
    elif name_dict is not None:
      return name_dict[script][self.index]
    else:
      return None

  def get_type(self):
    return NAME_TO_TYPE[self.anga_type_id]

  def __repr__(self):
    return "%s: %02d" % (self.anga_type_id, self.index)

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
    return "%s: %02d:%02d" % (self.anga_type_id, self.month.index, self.index)


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