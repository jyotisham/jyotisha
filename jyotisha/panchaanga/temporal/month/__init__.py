from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.zodiac import AngaSpan, NakshatraDivision
from sanskrit_data.schema.common import JsonObject


class LunarMonthAssigner(JsonObject):
  SIDERIAL_SOLAR_BASED = "SiderialSolarBasedAssigner"
  
  def __init__(self, panchaanga):
    self.panchaanga = panchaanga

  def assign(self):
    pass

  @classmethod
  def get_assigner(cls, assigner_id, panchaanga):
    if assigner_id == LunarMonthAssigner.SIDERIAL_SOLAR_BASED:
      return SiderialSolarBasedAssigner(panchaanga=panchaanga)
    else:
      raise ValueError("Invalid assigner_id " + assigner_id)


class SiderialSolarBasedAssigner(LunarMonthAssigner):
  def assign(self):
    """ Assigns Lunar months to days in the period
    
    Implementation note: Works by looking at solar months and new moons (which makes it easy to deduce adhika-mAsa-s.)
    
    :return: 
    """
    # tithi_sunrise[1] gives a rough indication of the number of days since last new moon. We now find a more precise interval below.
    last_new_moon = AngaSpan.find(
      self.panchaanga.jd_start - self.panchaanga.daily_panchaangas[1].tithi_at_sunrise - 3, self.panchaanga.jd_start - self.panchaanga.daily_panchaangas[1].tithi_at_sunrise + 3,
      zodiac.AngaType.TITHI, 30, ayanamsha_id=self.panchaanga.ayanamsha_id)
    this_new_moon = AngaSpan.find(
      last_new_moon.jd_start + 24, last_new_moon.jd_start + 32,
      zodiac.AngaType.TITHI, 30, ayanamsha_id=self.panchaanga.ayanamsha_id)

    # Check if current mAsa is adhika here
    is_adhika = NakshatraDivision(last_new_moon.jd_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_solar_raashi() == \
                NakshatraDivision(this_new_moon.jd_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_solar_raashi()

    # Keep on finding new moons in the period.
    last_d_assigned = 0
    while last_new_moon.jd_start < self.panchaanga.jd_start + self.panchaanga.duration + 1:
      next_new_moon = AngaSpan.find(
        this_new_moon.jd_start + 24, this_new_moon.jd_start + 32,
        zodiac.AngaType.TITHI, 30, ayanamsha_id=self.panchaanga.ayanamsha_id)

      # Loop over a month starting from this_new_moon.jd_end
      unassigned_days = range(last_d_assigned + 1, last_d_assigned + 32)
      for i in unassigned_days:
        last_solar_month = NakshatraDivision(this_new_moon.jd_end,
                                             ayanamsha_id=self.panchaanga.ayanamsha_id).get_solar_raashi()

        if i > self.panchaanga.duration + 1 or self.panchaanga.daily_panchaangas[i].jd_sunrise > this_new_moon.jd_end:
          last_d_assigned = i - 1
          break # out of unassigned days loop.

        if is_adhika:
          self.panchaanga.lunar_month[i] = (last_solar_month % 12) + .5
        else:
          self.panchaanga.lunar_month[i] = last_solar_month

      is_adhika = NakshatraDivision(this_new_moon.jd_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_solar_raashi() == \
                  NakshatraDivision(next_new_moon.jd_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_solar_raashi()
      last_new_moon.jd_start = this_new_moon.jd_start
      last_new_moon.jd_end = this_new_moon.jd_end
      this_new_moon.jd_start = next_new_moon.jd_start
      this_new_moon.jd_end = next_new_moon.jd_end
  