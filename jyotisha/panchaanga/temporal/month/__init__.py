import sys

from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.zodiac import AngaSpan, NakshatraDivision
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class LunarMonthAssigner(JsonObject):
  MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA = "MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA"
  
  def __init__(self, ayanaamsha_id):
    self.ayanaamsha_id = ayanaamsha_id

  def get_month_sunrise(self, daily_panchaanga):
    pass

  @classmethod
  def get_assigner(cls, computation_system):
    if computation_system.lunar_month_assigner_type == LunarMonthAssigner.MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA:
      return SiderialSolarBasedAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    else:
      raise ValueError("Invalid assigner_id " + computation_system.lunar_month_assigner_type)


class SiderialSolarBasedAssigner(LunarMonthAssigner):
  
  def get_month_sunrise(self, daily_panchaanga):
    """ Assigns Lunar months to days in the period
    
    Implementation note: Works by looking at solar months and new moons (which makes it easy to deduce adhika-mAsa-s.)
    
    :return: 
    """
    # tithi_at_sunrise gives a rough indication of the number of days since last new moon. We now find a more precise interval below.
    last_new_moon = AngaSpan.find(
      daily_panchaanga.jd_sunrise - daily_panchaanga.angas.tithi_at_sunrise - 3, daily_panchaanga.jd_sunrise - daily_panchaanga.angas.tithi_at_sunrise + 3,
      zodiac.AngaType.TITHI, 30, ayanaamsha_id=self.ayanaamsha_id)
    this_new_moon = AngaSpan.find(
      last_new_moon.jd_start + 24, last_new_moon.jd_start + 32,
      zodiac.AngaType.TITHI, 30, ayanaamsha_id=self.ayanaamsha_id)
    last_new_moon_solar_raashi = NakshatraDivision(last_new_moon.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    this_new_moon_solar_raashi = NakshatraDivision(this_new_moon.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    is_adhika = last_new_moon_solar_raashi == this_new_moon_solar_raashi

    if is_adhika:
      return (this_new_moon_solar_raashi % 12) + .5
    else:
      return this_new_moon_solar_raashi


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
