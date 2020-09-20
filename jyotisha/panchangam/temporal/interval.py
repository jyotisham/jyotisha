from math import floor

from sanskrit_data.schema import common


class Interval(common.JsonObject):
  def __init__(self, jd_start, jd_end):
    self.jd_start = jd_start
    self.jd_end = jd_end

  def to_tuple(self):
    return (self.jd_start, self.jd_end)


class TbSayanaMuhuurta(Interval):
  """ A muhUrta as defined by SayaNa's commentary to TB 5.3
  
  Refer https://archive.org/stream/Anandashram_Samskrita_Granthavali_Anandashram_Sanskrit_Series/ASS_037_Taittiriya_Brahmanam_with_Sayanabhashya_Part_1_-_Narayanasastri_Godbole_1934#page/n239/mode/2up .
  """

  def __init__(self, jd_start, jd_end, muhuurta_id):
    super().__init__(jd_start, jd_end)
    self.muhuurta_id = muhuurta_id
    self.ahna = floor(self.muhuurta_id / 3)
    self.ahna_part = self.muhuurta_id % 3
    self.is_nirviirya = self.muhuurta_id in (2, 3, 5, 6, 8, 9, 11, 12)

  def to_localized_string(self, city):
    from jyotisha.panchangam.temporal import Timezone
    return "muhUrta %d (nirvIrya: %s) starts from %s to %s" % (self.muhuurta_id, str(self.is_nirviirya),
                                                               Timezone(city.timezone).julian_day_to_local_time(
                                                                 julian_day=self.jd_start, round_seconds=True),
                                                               Timezone(city.timezone).julian_day_to_local_time(
                                                                 julian_day=self.jd_end, round_seconds=True))


def get_interval(start_jd, end_jd, part_index, num_parts):
  """Get start and end time of a given interval in a given span with specified fractions

  Args:
    :param start_jd float (jd)
    :param end_jd float (jd)
    :param part_index int, minimum/ start value 0
    :param num_parts

  Returns:
     tuple (start_time_jd, end_time_jd)

  Examples:

  """
  start_fraction = part_index / num_parts
  end_fraction = (part_index + 1) / num_parts

  start_time = start_jd + (end_jd - start_jd) * start_fraction
  end_time = start_jd + (end_jd - start_jd) * end_fraction

  return Interval(start_time, end_time)