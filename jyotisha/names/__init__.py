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

