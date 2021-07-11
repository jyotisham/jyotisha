import logging
import sys
from math import floor
from numbers import Number
from typing import Optional

import methodtools
import numpy
import swisseph as swe
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.interval import Interval, AngaSpan
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType, Anga
from jyotisha.util import default_if_none
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject
from scipy.optimize import brentq
from timebudget import timebudget


# noinspection SpellCheckingInspection
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class Ayanamsha(common.JsonObject):
  """
  
  rAShTriya panchAnga nakshatra ayanAmsha vs chitra at 180 :
  - Shaves off 3 seconds from typical panchaanga computation compared to precise chitrA tracking.
  - rAShTriya panchAnga nakshatra ayanAmsha tracks chitra fairly well. Still, it results in ~5 minutes differences in nakshatra spans.
  - chitrA does not move a lot in typical year, and it is mostly wasteful to compute its position fresh for every instant.
  """
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
    raise Exception("Bad ayanamsha_id")


class NakshatraDivision(common.JsonObject):
  """Nakshatra division at a certain time, according to a certain ayanaamsha."""

  def __init__(self, jd, ayanaamsha_id):
    super().__init__()
    self.ayanaamsha_id = ayanaamsha_id
    self.jd = jd

  def get_fractional_division_for_body(self, body: Graha, anga_type: AngaType) -> float:
    """
    
    :param body: graha ID.
    :return: 0.x for AshvinI and so on.
    """
    longitude = body.get_longitude(self.jd, ayanaamsha_id=self.ayanaamsha_id)
    return self.longitude_to_fractional_division(longitude=longitude, anga_type=anga_type)

  def get_equatorial_boundary_coordinates(self):
    """Get equatorial coordinates for the points where the ecliptic nakShatra boundary longitude intersects the ecliptic."""
    nakShatra_ends = ((numpy.arange(27) + 1) * (360.0 / 27.0) + Ayanamsha.singleton(
      self.ayanaamsha_id).get_offset(
      self.jd)) % 360
    equatorial_boundary_coordinates = [ecliptic_to_equatorial(longitude=longitude, latitude=0) for longitude in nakShatra_ends]
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

  def longitude_to_fractional_division(self, longitude, anga_type):
    return (longitude % 360) / anga_type.arc_length

  def get_anga_float(self, anga_type):
    """Returns the anga/ temporal property. Computed based on lunar and solar longitudes, division of a circle into a certain number of degrees (arc_len).

      Args:
        :param anga_type: One of the pre-defined tuple-valued constants in the panchaanga
        class, such as TITHI, nakshatra, YOGA, KARANA or SIDEREAL_MONTH

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

    lcalc = 0  # computing offset longitudes

    #  Get the lunar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_moon != 0:
      lmoon = Graha.singleton(Graha.MOON).get_longitude(self.jd, ayanaamsha_id=ayanaamsha_id)
      lcalc += w_moon * lmoon

    #  Get the solar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_sun != 0:
      lsun = Graha.singleton(Graha.SUN).get_longitude(self.jd, ayanaamsha_id=ayanaamsha_id)
      lcalc += w_sun * lsun

    return self.longitude_to_fractional_division(longitude=lcalc, anga_type=anga_type)

  def get_anga(self, anga_type):
    """Returns the anga prevailing at a particular time. Computed based on lunar and solar longitudes, division of a circle into a certain number of degrees (arc_len).

      Args:
        float arc_len: The arc_len for the corresponding anga

      Returns:
        int anga
    """

    return Anga.get_cached(index=int(1 + floor(self.get_anga_float(anga_type))), anga_type_id=anga_type.name)

  def get_all_angas(self):
    """Compute various properties of the time based on lunar and solar longitudes, division of a circle into a certain number of degrees (arc_len).
    """
    anga_objects = [AngaType.TITHI, AngaType.TITHI_PADA, AngaType.NAKSHATRA, AngaType.NAKSHATRA_PADA, AngaType.RASHI,
                    AngaType.SIDEREAL_MONTH, AngaType.SOLAR_NAKSH, AngaType.YOGA, AngaType.KARANA]
    angas = list(map(lambda anga_object: self.get_anga(anga_type=anga_object), anga_objects))
    anga_ids = list(map(lambda anga_obj: anga_obj.index, anga_objects))
    return dict(list(zip(anga_ids, angas)))

  def get_nakshatra(self):
    """Returns the nakshatra prevailing at a given moment

    Nakshatra is computed based on the longitude of the Moon; in
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

    return self.get_anga(AngaType.SIDEREAL_MONTH)


def longitude_to_right_ascension(longitude):
  return (360 - longitude) / 360 * 24


def ecliptic_to_equatorial(longitude, latitude):
  coordinates = swe.cotrans(lon=longitude, lat=latitude, dist=9999999, obliquity=23.437404)
  # swe.cotrans returns the right ascension longitude in degrees, rather than hours.
  return (
    longitude_to_right_ascension(coordinates[0]), coordinates[1])


class AngaSpanFinder(JsonObject):
  def __init__(self, ayanaamsha_id, anga_type):
    super(AngaSpanFinder, self).__init__()
    self.ayanaamsha_id = ayanaamsha_id
    self.anga_type = anga_type

  @methodtools.lru_cache(maxsize=None)
  @classmethod
  def get_cached(cls, ayanaamsha_id, anga_type):
    return AngaSpanFinder(ayanaamsha_id=ayanaamsha_id, anga_type=anga_type)

  def _get_anga(self, jd):
    return NakshatraDivision(jd, ayanaamsha_id=self.ayanaamsha_id).get_anga( anga_type=self.anga_type)

  def _get_anga_float_offset(self, jd, target_anga):
    anga_float = NakshatraDivision(jd, ayanaamsha_id=self.ayanaamsha_id).get_anga_float(anga_type=self.anga_type)
    num_angas = self.anga_type.num_angas
    if anga_float > target_anga.index:
      return anga_float - num_angas # A negative number
    else:
      return anga_float - (target_anga.index - 1)

  def _interpolate_for_start(self, jd1, jd2, target_anga):
    try:
      # noinspection PyTypeChecker
      return brentq(lambda x: self._get_anga_float_offset(jd=x, target_anga=target_anga), jd1, jd2)
    except ValueError:
      return None

  def find_anga_start_between(self, jd1, jd2, target_anga):
    jd_start = None
    num_angas = self.anga_type.num_angas
    min_step = 0.5 * self.anga_type.mean_period_days/num_angas  # Min Step for moving - half an anga span.
    jd_bracket_L = jd1
    jd_now = jd1
    while jd_now <= jd2 and jd_start is None:
      anga_now = self._get_anga(jd=jd_now)

      if anga_now < target_anga:
        # So, jd_now will be lower than jd_start
        jd_bracket_L = jd_now
      if anga_now == target_anga:
        # In this branch, anga_now will have overshot the jd_start of the required interval.
        jd_start = self._interpolate_for_start(jd1=jd_bracket_L, jd2=jd_now, target_anga=target_anga)
      if jd_now == jd2:
        # Prevent infinite loop
        break
      jd_now = min(jd_now + min_step, jd2)
    return jd_start

  @timebudget
  def find(self, jd1: float, jd2: float, target_anga_id: int) -> Optional[AngaSpan]:
    """Computes anga spans for sunrise_day_angas such as tithi, nakshatra, yoga
        and karana.

        Args:
          :param jd1: return the first span that starts after this date
          :param jd2: return the first span that ends before this date

        Returns:
          None if target_anga_id was not found
          Interval, with boundary jds None if they don't occur within [jd1, jd2] 
    """
    if isinstance(target_anga_id, Number):
      # TODO: Remove this backward compatibility fix
      target_anga = Anga.get_cached(index=target_anga_id, anga_type_id=self.anga_type.name)
    else:
      target_anga = target_anga_id

    anga_interval = AngaSpan(jd_start=None, jd_end=None, anga=target_anga)

    anga_interval.jd_start = self.find_anga_start_between(jd1=jd1, jd2=jd2, target_anga=target_anga)

    next_anga = target_anga + 1
    anga_interval.jd_end = self.find_anga_start_between(jd1=default_if_none(anga_interval.jd_start, jd1), jd2=jd2, target_anga=next_anga)
    if anga_interval.jd_start is None and anga_interval.jd_end is None:
      if self._get_anga(jd=jd1) != target_anga:
        return None
    return anga_interval

  @timebudget
  def get_spans_in_period(self, jd_start, jd_end, target_anga_id):
    if jd_start > jd_end:
      raise ValueError((jd_start, jd_end))
    jd_bracket_L = jd_start
    spans = []
    while jd_bracket_L <= jd_end:
      # A whole period plus 4 angas beyond jd_bracket_L, which might be 2 angas behind the target anga.
      jd_bracket_R = min(jd_bracket_L + (1 + 4.0/self.anga_type.num_angas) * self.anga_type.mean_period_days, jd_end)
      span = self.find(
        jd1=jd_bracket_L, jd2=jd_bracket_R,
        target_anga_id=target_anga_id)
      if span is None:
        break
      else:
        spans.append(span)
        # A whole period minus 2 angas as the next seek boundary
        jd_bracket_L = default_if_none(span.jd_start, jd_bracket_L) + self.anga_type.mean_period_days * (1 - 2.0 / self.anga_type.num_angas)
    return spans

  @timebudget
  def get_all_angas_in_period(self, jd1, jd2):
    spans = []
    jd_start = None
    anga_now = self._get_anga(jd=jd1)
    while default_if_none(jd_start, jd1) <= jd2:
      next_anga = anga_now + 1
      jd_end = self.find_anga_start_between(target_anga=next_anga, jd1=default_if_none(jd_start, jd1), jd2=jd2)
      spans.append(AngaSpan(jd_start=jd_start, jd_end=jd_end, anga=anga_now))
      if jd_end is None:
        break
      else:
        anga_now = next_anga
        jd_start = jd_end
    return spans


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])


def get_tropical_month(jd):
  nd = NakshatraDivision(jd=jd, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
  return nd.get_anga(anga_type=AngaType.TROPICAL_MONTH)


def get_previous_solstice_month_span(jd):
  """Get the previous solstice (especially the tropical month id and the jd.)
  
  Returns an AngaSpan object.
  """
  tropical_month = get_tropical_month(jd=jd)
  if tropical_month.index >= 4 and tropical_month.index < 10:
    target_month_id = 4
  else:
    target_month_id = 10
  months_past_solstice = (tropical_month - target_month_id) % 12
  jd1 = jd - (months_past_solstice * 30 + months_past_solstice + 35)
  jd2 = jd - (months_past_solstice * 30 + months_past_solstice) + 35
  anga_span_finder = AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=AngaType.TROPICAL_MONTH)
  anga_span = anga_span_finder.find(jd1=jd1, jd2=jd2, target_anga_id=target_month_id)
  return anga_span


if __name__ == '__main__':
  # lahiri_nakshatra_division = NakshatraDivision(jd=temporal.utc_to_jd(year=2017, month=8, day=19, hour=11, minutes=10, seconds=0, flag=1)[0])
  pass
