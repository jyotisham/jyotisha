import swisseph as swe

# These are present in http://www.astro.com/swisseph/swephprg.htm#_Toc471829094 but not in the swe python module.
SIDM_TRUE_PUSHYA = 29
SIDM_TRUE_MULA = 35


def get_ayanamsha_name(ayanamsha_id):
  if ayanamsha_id == SIDM_TRUE_MULA:
    return "true mula"
  if ayanamsha_id == SIDM_TRUE_PUSHYA:
    return "true pushya"
  return swe.get_ayanamsa_name(ayanamsha_id)


class Graha(object):
  SUN = "sun"
  MOON = "moon"
  JUPITER = "jupiter"
  VENUS = "venus"
  MERCURY = "mercury"
  MARS = "mars"
  SATURN = "saturn"

  @classmethod
  def get_swisseph_id(cls, body_name):
    body_id = -1
    if body_name == cls.SUN:
      body_id = swe.SUN
    elif body_name == cls.MOON:
      body_id = swe.MOON
    elif body_name == cls.JUPITER:
      body_id = swe.JUPITER
    elif body_name == cls.VENUS:
      body_id = swe.VENUS
    elif body_name == cls.MERCURY:
      body_id = swe.MERCURY
    elif body_name == cls.MARS:
      body_id = swe.MARS
    elif body_name == "saturn":
      body_id = swe.SATURN
    return body_id