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


def get_swisseph_body_id(body_name):
  body_id = -1
  if body_name == "sun":
    body_id = swe.SUN
  elif body_name == "moon":
    body_id = swe.MOON
  elif body_name == "jupiter":
    body_id = swe.JUPITER
  elif body_name == "venus":
    body_id = swe.VENUS
  elif body_name == "mercury":
    body_id = swe.MERCURY
  elif body_name == "mars":
    body_id = swe.MARS
  elif body_name == "saturn":
    body_id = swe.SATURN
  return body_id