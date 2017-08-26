import swisseph as swe
import numpy
import logging

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
    self.right_boundaries = ((numpy.arange(27) + 1) * (360/27) + swe.get_ayanamsa(julday)) % 360

  def get_nakshatra(self, body_id, julday=-1):
    if julday > -1:
      self.set_time(julday=julday)
    return (swe.calc_ut(self.julday, body_id)[0] - swe.get_ayanamsa(self.julday)) % 360

  def __str__(self):
    return str(self.__dict__)

  # def get_boundary_longitudes(self):
  #   map(lambda longitude: , self.right_boundaries.tolist(), xyz)


if __name__ == '__main__':
  lahiri_nakshatra_division = NakshatraDivision(julday=swe.julday(2017,8,3))
  logging.info(lahiri_nakshatra_division)
  #  input: long., lat., dist., tilt of the ecliptic.
  logging.debug(swe.cotrans(lon=200, lat=-90, dist=9999999, obliquity=23.437404))
