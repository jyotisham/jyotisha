import swisseph as swe


class Graha(object):
  SUN = "sun"
  MOON = "moon"
  JUPITER = "jupiter"
  VENUS = "venus"
  MERCURY = "mercury"
  MARS = "mars"
  SATURN = "saturn"

  def __init__(self, body_name):
      self.body_name = body_name

  def _get_swisseph_id(self):
    body_id = -1
    if self.body_name == Graha.SUN:
      body_id = swe.SUN
    elif self.body_name == Graha.MOON:
      body_id = swe.MOON
    elif self.body_name == Graha.JUPITER:
      body_id = swe.JUPITER
    elif self.body_name == Graha.VENUS:
      body_id = swe.VENUS
    elif self.body_name == Graha.MERCURY:
      body_id = swe.MERCURY
    elif self.body_name == Graha.MARS:
      body_id = swe.MARS
    elif self.body_name == Graha.SATURN:
      body_id = swe.SATURN
    return body_id

  def get_longitude(self, jd):
      return swe.calc_ut(jd, self._get_swisseph_id())[0][0]