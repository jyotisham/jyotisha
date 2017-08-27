import swisseph as swe
import numpy
import logging

from jyotisha.panchangam import temporal

from jyotisha import custom_transliteration

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)



class NakshatraDivision(object):
  """Nakshatra division at a certain time, according to a certain ayanaamsha."""

  def __init__(self, julday, ayanamsha_id=swe.SIDM_LAHIRI):
    self.ayanamsha_id=ayanamsha_id
    swe.set_sid_mode(ayanamsha_id)
    self.set_time(julday=julday)

  def set_time(self, julday):
    self.julday = julday
    self.right_boundaries = ((numpy.arange(27) + 1) * (360.0/27.0) + swe.get_ayanamsa(julday)) % 360

  def get_nakshatra(self, body_id, julday=None):
    if julday is not None:
      self.set_time(julday=julday)

    return (((swe.calc_ut(self.julday, body_id)[0] - swe.get_ayanamsa(self.julday)) % 360) / (360.0/27.0))

  def __str__(self):
    return str(self.__dict__)

  def get_equatorial_boundary_coordinates(self):
    """Get equatorial coordinates for the points where the ecliptic nakShatra boundary longitude intersects the ecliptic."""
    equatorial_boundary_coordinates = [swe.cotrans(lon=longitude, lat=0, dist=9999999, obliquity=23.437404) for longitude in self.right_boundaries]
    # swe.cotrans returns the right ascension longitude in degrees, rather than hours.
    equatorial_boundary_coordinates_with_ra = [(custom_transliteration.longitudeToRightAscension(longitude), declination) for (longitude, declination, distance) in equatorial_boundary_coordinates]
    return equatorial_boundary_coordinates_with_ra

  def get_stellarium_nakshatra_boundaries(self):
    equatorial_boundary_coordinates_with_ra = self.get_equatorial_boundary_coordinates()
    ecliptic_north_pole = swe.cotrans(lon=20, lat=90, dist=9999999, obliquity=23.437404)
    ecliptic_north_pole_with_ra = (custom_transliteration.longitudeToRightAscension(ecliptic_north_pole[0]), ecliptic_north_pole[1])
    # logging.debug(ecliptic_north_pole_with_ra)
    ecliptic_south_pole = swe.cotrans(lon=20, lat=-90, dist=9999999, obliquity=23.437404)
    ecliptic_south_pole_with_ra = (custom_transliteration.longitudeToRightAscension(ecliptic_south_pole[0]), ecliptic_south_pole[1])
    # logging.debug(ecliptic_south_pole_with_ra)
    for index, (boundary_ra, boundary_declination) in enumerate(equatorial_boundary_coordinates_with_ra):
      print('3 %(north_pole_ra)f %(north_pole_dec)f %(boundary_ra)f %(boundary_declination)f %(south_pole_ra)f %(south_pole_dec)f 2 N%(sector_id_1)02d N%(sector_id_2)02d' % dict(
        north_pole_ra=ecliptic_north_pole_with_ra[0],
        north_pole_dec=ecliptic_north_pole_with_ra[1],
        boundary_ra=boundary_ra,
        boundary_declination=boundary_declination,
        south_pole_ra=ecliptic_south_pole_with_ra[0],
        south_pole_dec=ecliptic_south_pole_with_ra[1],
        sector_id_1=(index%27 + 1),
        sector_id_2=((index+1)%27 + 1)
      ))



if __name__ == '__main__':
  # lahiri_nakshatra_division = NakshatraDivision(julday=swe.utc_to_jd(year=2017, month=8, day=19, hour=11, minutes=10, seconds=0, flag=1)[0])
  lahiri_nakshatra_division = NakshatraDivision(julday=swe.utc_to_jd(year=1982, month=2, day=19, hour=11, minutes=10, seconds=0, flag=1)[0])
  logging.info(lahiri_nakshatra_division.get_nakshatra(body_id=swe.MOON))
  # logging.info(lahiri_nakshatra_division)
  # logging.debug(swe.cotrans(lon=20, lat=-90, dist=9999999, obliquity=23.437404))
  lahiri_nakshatra_division.get_stellarium_nakshatra_boundaries()
