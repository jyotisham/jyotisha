import logging
import sys
from math import floor

import methodtools
import numpy
import swisseph as swe
from scipy.optimize import brentq

from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.interval import Interval
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

# noinspection SpellCheckingInspection
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class Ayanamsha(common.JsonObject):
  VERNAL_EQUINOX_AT_0 = "VERNAL_EQUINOX_AT_0"
  CHITRA_AT_180 = "CHITRA_AT_180"
  ASHVINI_STARTING_0 = "ASHVINI_STARTING_0"
  RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING = "RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING"

  @methodtools.lru_cache(maxsize=None)
  @classmethod
  def singleton(cls, ayanaamsha_id):
    return cls(ayanaamsha_id=ayanaamsha_id)

  def __init__(self, ayanaamsha_id):
    super().__init__()
    self.ayanaamsha_id = ayanaamsha_id

  def get_offset(self, jd):
    if self.ayanaamsha_id == Ayanamsha.VERNAL_EQUINOX_AT_0:
      return 0
    elif self.ayanaamsha_id == Ayanamsha.CHITRA_AT_180:
      # TODO: The below fails due to https://github.com/astrorigin/pyswisseph/issues/35
      from jyotisha.panchaanga.temporal import body
      return body.get_star_longitude(star="Spica", jd=jd) - 180
    elif self.ayanaamsha_id == Ayanamsha.ASHVINI_STARTING_0:
      return 0
    elif self.ayanaamsha_id == Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING:
      swe.set_sid_mode(swe.SIDM_LAHIRI)
      return swe.get_ayanamsa_ut(jd)
    raise Exception("Bad ayamasha_id")


class NakshatraDivision(common.JsonObject):
  """Nakshatra division at a certain time, according to a certain ayanaamsha."""

  def __init__(self, julday, ayanaamsha_id):
    super().__init__()
    self.ayanaamsha_id = ayanaamsha_id

    self.set_time(julday=julday)

  # noinspection PyAttributeOutsideInit
  def set_time(self, julday):
    self.julday = julday
    self.right_boundaries = ((numpy.arange(27) + 1) * (360.0 / 27.0) + Ayanamsha.singleton(
      self.ayanaamsha_id).get_offset(
      julday)) % 360

  def get_nakshatra_for_body(self, body):
    """
    
    :param body: graha ID.
    :return: 1.x for AshvinI and so on.
    """
    if self.julday is not None:
      self.set_time(julday=self.julday)
    logging.debug(Ayanamsha.singleton(self.ayanaamsha_id).get_offset(self.julday))
    return Graha.singleton(body).get_longitude(self.julday, ayanaamsha_id=self.ayanaamsha_id) / (360.0 / 27.0) + 1

  def get_equatorial_boundary_coordinates(self):
    """Get equatorial coordinates for the points where the ecliptic nakShatra boundary longitude intersects the ecliptic."""
    equatorial_boundary_coordinates = [ecliptic_to_equatorial(longitude=longitude, latitude=0) for longitude in
                                       self.right_boundaries]
    return equatorial_boundary_coordinates

  def get_stellarium_nakshatra_boundaries(self):
    equatorial_boundary_coordinates_with_ra = self.get_equatorial_boundary_coordinates()
    ecliptic_north_pole_with_ra = ecliptic_to_equatorial(longitude=20, latitude=90)
    # logging.debug(ecliptic_north_pole_with_ra)
    ecliptic_south_pole_with_ra = ecliptic_to_equatorial(longitude=20, latitude=-90)
    # logging.debug(ecliptic_south_pole_with_ra)
    for index, (boundary_ra, boundary_declination) in enumerate(equatorial_boundary_coordinates_with_ra):
      print(
        '3 %(north_pole_ra)f %(north_pole_dec)f %(boundary_ra)f %(boundary_declination)f %(south_pole_ra)f %(south_pole_dec)f 2 N%(sector_id_1)02d N%(sector_id_2)02d' % dict(
          north_pole_ra=ecliptic_north_pole_with_ra[0],
          north_pole_dec=ecliptic_north_pole_with_ra[1],
          boundary_ra=boundary_ra,
          boundary_declination=boundary_declination,
          south_pole_ra=ecliptic_south_pole_with_ra[0],
          south_pole_dec=ecliptic_south_pole_with_ra[1],
          sector_id_1=(index % 27 + 1),
          sector_id_2=((index + 1) % 27 + 1)
        ))

  def get_anga_float(self, anga_type):
    """Returns the anga/ temporal property. Computed based on lunar and solar longitudes, division of a circle into a certain number of degrees (arc_len).

      Args:
        :param anga_type: One of the pre-defined tuple-valued constants in the panchaanga
        class, such as TITHI, NAKSHATRAM, YOGA, KARANAM or SOLAR_MONTH

      Returns:
        float anga
    """
    if anga_type == AngaType.TITHI:
      # For efficiency - avoid lookups.
      ayanaamsha_id = Ayanamsha.VERNAL_EQUINOX_AT_0
    else:
      ayanaamsha_id = self.ayanaamsha_id

    w_moon = anga_type.weight_moon
    w_sun = anga_type.weight_sun
    arc_len = anga_type.arc_length

    lcalc = 0  # computing offset longitudes

    #  Get the lunar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_moon != 0:
      lmoon = Graha.singleton(Graha.MOON).get_longitude(self.julday, ayanaamsha_id=ayanaamsha_id)
      lcalc += w_moon * lmoon

    #  Get the solar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_sun != 0:
      lsun = Graha.singleton(Graha.SUN).get_longitude(self.julday, ayanaamsha_id=ayanaamsha_id)
      lcalc += w_sun * lsun

    lcalc = lcalc % 360

    return lcalc / arc_len

  def get_anga(self, anga_type):
    """Returns the anga prevailing at a particular time. Computed based on lunar and solar longitudes, division of a circle into a certain number of degrees (arc_len).

      Args:
        float arc_len: The arc_len for the corresponding anga

      Returns:
        int anga
    """

    return int(1 + floor(self.get_anga_float(anga_type)))

  def get_all_angas(self):
    """Compute various properties of the time based on lunar and solar longitudes, division of a circle into a certain number of degrees (arc_len).
    """
    anga_objects = [AngaType.TITHI, AngaType.TITHI_PADA, AngaType.NAKSHATRA, AngaType.NAKSHATRA_PADA, AngaType.RASHI,
                    AngaType.SOLAR_MONTH, AngaType.SOLAR_NAKSH, AngaType.YOGA, AngaType.KARANA]
    angas = list(map(lambda anga_object: self.get_anga(anga_type=anga_object), anga_objects))
    anga_ids = list(map(lambda anga_obj: anga_obj.name, anga_objects))
    return dict(list(zip(anga_ids, angas)))

  def get_nakshatra(self):
    """Returns the nakshatram prevailing at a given moment

    Nakshatram is computed based on the longitude of the Moon; in
    addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted.

    Returns:
      int nakShatram, where 1 stands for Ashwini, ..., 14 stands
      for Chitra, ..., 27 stands for Revati

    """

    return self.get_anga(AngaType.NAKSHATRA)

  def get_yoga(self):
    """Returns the yoha prevailing at a given moment

    Yoga is computed based on the longitude of the Moon and longitude of
    the Sun; in addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted (for each).

    Returns:
      int yoga, where 1 stands for Vishkambha and 27 stands for Vaidhrti
    """

    return self.get_anga(AngaType.YOGA)

  def get_solar_raashi(self):
    """Returns the solar rashi prevailing at a given moment

    Solar month is computed based on the longitude of the sun; in
    addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted.

    Returns:
      int rashi, where 1 stands for mESa, ..., 12 stands for mIna
    """

    return self.get_anga(AngaType.SOLAR_MONTH)


def longitude_to_right_ascension(longitude):
  return (360 - longitude) / 360 * 24


def ecliptic_to_equatorial(longitude, latitude):
  coordinates = swe.cotrans(lon=longitude, lat=latitude, dist=9999999, obliquity=23.437404)
  # swe.cotrans returns the right ascension longitude in degrees, rather than hours.
  return (
    longitude_to_right_ascension(coordinates[0]), coordinates[1])


class AngaType(JsonObject):
  # The below class variables are declared here, but instantiated later.
  TITHI = None
  TITHI_PADA = None
  NAKSHATRA = None
  NAKSHATRA_PADA = None
  RASHI = None
  YOGA = None
  KARANA = None
  SOLAR_MONTH = None
  SOLAR_NAKSH = None
  SOLAR_NAKSH_PADA = None

  def __init__(self, name, arc_length, weight_moon, weight_sun):
    super(AngaType, self).__init__()
    self.name = name
    self.arc_length = arc_length
    self.weight_moon = weight_moon
    self.weight_sun = weight_sun


AngaType.TITHI = AngaType(name='TITHI', arc_length=360.0 / 30.0, weight_moon=1, weight_sun=-1)
AngaType.TITHI_PADA = AngaType(name='TITHI_PADA', arc_length=360.0 / 120.0, weight_moon=1, weight_sun=-1)
AngaType.NAKSHATRA = AngaType(name='NAKSHATRAM', arc_length=360.0 / 27.0, weight_moon=1, weight_sun=0)
AngaType.NAKSHATRA_PADA = AngaType(name='NAKSHATRA_PADA', arc_length=360.0 / 108.0, weight_moon=1, weight_sun=0)
AngaType.RASHI = AngaType(name='RASHI', arc_length=360.0 / 12.0, weight_moon=1, weight_sun=0)
AngaType.YOGA = AngaType(name='YOGA', arc_length=360.0 / 27.0, weight_moon=1, weight_sun=1)
AngaType.KARANA = AngaType(name='KARANAM', arc_length=360.0 / 60.0, weight_moon=1, weight_sun=-1)
AngaType.SOLAR_MONTH = AngaType(name='SOLAR_MONTH', arc_length=360.0 / 12.0, weight_moon=0, weight_sun=1)
AngaType.SOLAR_NAKSH = AngaType(name='SOLAR_NAKSH', arc_length=360.0 / 27.0, weight_moon=0, weight_sun=1)
AngaType.SOLAR_NAKSH_PADA = AngaType(name='SOLAR_NAKSH_PADA', arc_length=360.0 / 108.0, weight_moon=0, weight_sun=1)


class AngaSpanFinder(JsonObject):
  def __init__(self, ayanaamsha_id, anga_type):
    self.ayanaamsha_id = ayanaamsha_id
    self.anga_type = anga_type

  def _get_anga(self, jd):
    return NakshatraDivision(jd, ayanaamsha_id=self.ayanaamsha_id).get_anga( anga_type=self.anga_type)

  def _get_anga_float_offset(self, jd, target_anga_id):
    anga_float = NakshatraDivision(jd, ayanaamsha_id=self.ayanaamsha_id).get_anga_float(anga_type=self.anga_type)
    num_angas = int(360.0 / self.anga_type.arc_length)
    if anga_float > target_anga_id:
      return anga_float - num_angas # A negative number
    else:
      return anga_float - (target_anga_id-1)

  def _interpolate_for_start(self, jd1, jd2, target_anga_id):
    try:
      # noinspection PyTypeChecker
      return brentq(lambda x: self._get_anga_float_offset(jd=x, target_anga_id=target_anga_id), jd1, jd2)
    except ValueError:
      return None

  def find_anga_start_between(self, jd1, jd2, target_anga_id):
    jd_start = None
    num_angas = int(360.0 / self.anga_type.arc_length)
    min_step = 0.5  # Min Step for moving
    jd_bracket_L = jd1
    jd_now = jd1
    while jd_now <= jd2 and jd_start is None:
      anga_now = self._get_anga(jd=jd_now)

      if anga_now < target_anga_id or (target_anga_id == 1 and anga_now == num_angas):
        # So, jd_now will be lower than jd_start
        jd_bracket_L = jd_now
      if anga_now == target_anga_id:
        # In this branch, anga_now will have overshot the jd_start of the required interval.
        jd_start = self._interpolate_for_start(jd1=jd_bracket_L, jd2=jd_now, target_anga_id=target_anga_id)
      if jd_now == jd2:
        # Prevent infinite loop
        break
      jd_now = min(jd_now + min_step, jd2)
    return jd_start

  def find(self, jd1: float, jd2: float, target_anga_id: int):
    """Computes anga spans for angas such as tithi, nakshatram, yoga
        and karanam.

        Args:
          :param jd1: return the first span that starts after this date
          :param jd2: return the first span that ends before this date
          :param anga_type: TITHI, NAKSHATRAM, YOGA, KARANAM, SOLAR_MONTH, SOLAR_NAKSH
          :param ayanaamsha_id
          :param debug

        Returns:
          tuple: A tuple of start and end times that lies within jd1 and jd2
    """
    num_angas = int(360.0 / self.anga_type.arc_length)
    if target_anga_id > num_angas or target_anga_id < 1:
      raise ValueError

    anga_interval = AngaSpan(jd_start=None, jd_end=None, name=target_anga_id)

    anga_interval.jd_start = self.find_anga_start_between(jd1=jd1, jd2=jd2, target_anga_id=target_anga_id)

    if anga_interval.jd_start is None:
      return AngaSpan(jd_start=None, jd_end=None, name=target_anga_id)  # If it doesn't start, we don't care if it ends!

    anga_id_after_target = (target_anga_id % num_angas) + 1
    anga_interval.jd_end = self.find_anga_start_between(jd1=anga_interval.jd_start, jd2=jd2, target_anga_id=anga_id_after_target)
    return anga_interval


class AngaSpan(Interval):
  @classmethod
  def find(cls, jd1: float, jd2: float, anga_type: AngaType, target_anga_id: int, ayanaamsha_id: str, debug: bool = False):
    """Computes anga spans for angas such as tithi, nakshatram, yoga
        and karanam.

        Args:
          :param jd1: return the first span that starts after this date
          :param jd2: return the first span that ends before this date
          :param anga_type: TITHI, NAKSHATRAM, YOGA, KARANAM, SOLAR_MONTH, SOLAR_NAKSH
          :param ayanaamsha_id
          :param debug

        Returns:
          tuple: A tuple of start and end times that lies within jd1 and jd2
    """
    anga_span_finder = AngaSpanFinder(ayanaamsha_id=ayanaamsha_id, anga_type=anga_type)
    return anga_span_finder.find(jd1=jd1, jd2=jd2, target_anga_id=target_anga_id)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])


if __name__ == '__main__':
  # lahiri_nakshatra_division = NakshatraDivision(julday=temporal.utc_to_jd(year=2017, month=8, day=19, hour=11, minutes=10, seconds=0, flag=1)[0])
  pass
