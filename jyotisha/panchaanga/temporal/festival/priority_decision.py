"""
Main function in this module is the :func:`decide` function.

"""

import logging

from jyotisha.panchaanga.temporal import zodiac, get_2_day_interval_boundary_angas
from jyotisha.util import default_if_none


class FestivalDecision(object):
  def __init__(self, fday, day_panchaanga=None, boundary_angas=None):
    self.boundary_angas = boundary_angas
    self.day_panchaanga = day_panchaanga
    self.fday = fday


  @classmethod
  def from_details(cls, boundary_angas_list, fday, panchaangas):
    if fday is None:
      return None
    else:
      if fday == -1:
        boundary_angas = None
        day_panchaanga = None
      else:
        boundary_angas = boundary_angas_list[fday]
        day_panchaanga = panchaangas[fday]
      return FestivalDecision(day_panchaanga=day_panchaanga, boundary_angas=boundary_angas, fday=fday)


def decide_paraviddha(p0, p1, target_anga, kaala):
  (d0_angas, d1_angas) = get_2_day_interval_boundary_angas(kaala=kaala, anga_type=target_anga.get_type(), p0=p0, p1=p1)
  prev_anga = target_anga - 1
  next_anga = target_anga + 1

  if (d0_angas.end == target_anga and d1_angas.end == target_anga) or (
      d1_angas.start == target_anga and d1_angas.end == target_anga):
    # Incident at kaala on two consecutive days; so take second
    fday = 1
  elif d0_angas.start == target_anga and d0_angas.end == target_anga and d1_angas.start == target_anga:
    # Incident on day 1, and touching day 2
    if d1_angas.interval.name in ['प्रातः']:
      fday = 0
    else:
      fday = 1
  elif d0_angas.start == target_anga and d0_angas.end == target_anga:
    fday = 0
  elif d0_angas.end == target_anga and d1_angas.start != target_anga:
    # d0 only touches target_anga right at its own kaala-end (a brief trailing touch), and d1's kaala
    # does not touch it at all -- an exclusive, unambiguous claim for d0.
    fday = 0
  elif d1_angas.start == target_anga:
    if d1_angas.interval.name in ['प्रातः']:
      fday = 0
    else:
      fday = 1
  elif d0_angas.start == target_anga and d0_angas.end == next_anga:
    if d0_angas.interval.name in ['अपराह्णः']:
      fday = 0
    else:
      # Example when this branch is active: 2019 'madhurakavi AzhvAr tirunakSattiram': sidereal_solar_month 1, nakshatra 14 paraviddha praatah.
      # Instead of setting fday = 0 - 1 , we set it to None - since we only care about deciding between p0 and p1. Assignments to the previous day will have happened in the previous invocation (deciding between p(-1) and p0.)
      fday = None
  elif d0_angas.end == prev_anga and d1_angas.start == next_anga:
    fday = 0
  else:
    fday = None
    # Expected example:  (19, 19), (19, 20), 20
    # logging.debug("paraviddha: %s, %s, %s - Not assigning a festival this day. Likely checking on the wrong day pair.", str(d0_angas.to_tuple()), str(d1_angas.to_tuple()), str(target_anga.index))

  return FestivalDecision.from_details(boundary_angas_list=[d0_angas, d1_angas], fday=fday, panchaangas=[p0, p1])


def decide_puurvaviddha(p0, p1, target_anga, kaala):
  (d0_angas, d1_angas) = get_2_day_interval_boundary_angas(kaala=kaala, anga_type=target_anga.get_type(), p0=p0, p1=p1)
  kaala = d0_angas.interval.name
  prev_anga = target_anga - 1
  next_anga = target_anga + 1
  if d0_angas.start >= target_anga or d0_angas.end >= target_anga:
    fday = 0
  elif d1_angas.start == target_anga or d1_angas.end == target_anga:
    fday = 0 + 1
  else:
    # This means that the correct anga did not
    # touch the kaala on either day!
    if d0_angas.end == prev_anga and d1_angas.start == next_anga:
      # The following may need per-festival assignment, but this is reasonable, typically
      # TODO: eliminate sunrise and moonrise below.
      d_offset_map = {'सूर्योदयः': 0, 'sunrise': 0,  'चन्द्रोदयः': 0, 'moonrise': 0, 'पूर्वाह्णः': 0, 'प्रातः': 0, 'साङ्गवः': 0, 'चैत्रः': 0, 'मध्याह्नः': 1,
                      'मध्याह्नः~(त्रेधा)': 1, 'अपराह्णः': 1, 'सायाह्नः': 1, 'मध्यरात्रिः': 1, 'रात्रिमानम्': 1,
                      'सूर्यास्तमयः': 1, 'sunset': 1, 'प्रदोषः': 1, 'पूर्वरात्रिः~(त्रेधा)': 1, 'निशीथः': 1, 'प्राक्तनारुणोदयः': 1}
      if kaala not in d_offset_map.keys():
        logging.error(f"Could not find {kaala}")
      d_offset = d_offset_map[kaala]
      # Need to assign a day to the festival here
      # since the anga did not touch kaala on either day
      # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
      # THIS BEING PURVAVIDDHA
      # Perhaps just need better checking of
      # conditions instead of this fix
      fday = 0 + d_offset
    else:
      # Expected example:  (25, 25), (25, 25), 26
      # logging.debug("puurvaviddha: %s, %s, %s - Not assigning a festival this day. Likely the next then.", str(d0_angas.to_tuple()), str(d1_angas.to_tuple()), str(target_anga.index))
      fday = None
  return FestivalDecision.from_details(boundary_angas_list=[d0_angas, d1_angas], fday=fday, panchaangas=[p0, p1])


def compare_vyaapti_duration(d0_angas, d1_angas, target_anga, ayanaamsha_id):
  """ Compares the target anga's true duration overlap with d0's vs d1's kaala, for cases where boundary
  sampling alone can't distinguish the two (eg. both fully cover their kaala, or the anga only touches the
  shared boundary between the two kaalas). Returns 0 or 1 (the day with the greater overlap).
  """
  if d0_angas.interval.name == 'अपराह्णः' and d0_angas.start == target_anga and d0_angas.end == target_anga and d1_angas.start == target_anga and d1_angas.end == target_anga:
    # Both d0 and d1 fully cover aparaahna -- an unusually long-duration anga spanning both days' kaalas
    # in full. Traditional practice (this is typically a shraaddha-type observance) is to prefer the
    # second day outright here, rather than compare true durations -- and rather than lean on day-length
    # (ahas) trend, since ahas only increases toward the second day for part of the year.
    return 1

  anga_span = zodiac.AngaSpanFinder(ayanaamsha_id=ayanaamsha_id, anga_type=target_anga.get_type()).find(jd1=d0_angas.interval.jd_start, jd2=d1_angas.interval.jd_end, target_anga_id=target_anga)
  # A None boundary means the anga's true start/end lies outside [jd1, jd2] in that direction (eg. it started
  # before d0's kaala even began) -- clamp to the search window's own edge, which is the correct "at least
  # this much" measure for comparison purposes here.
  anga_start = default_if_none(anga_span.jd_start, d0_angas.interval.jd_start)
  anga_end = default_if_none(anga_span.jd_end, d1_angas.interval.jd_end)
  vyapti_0 = max(d0_angas.interval.jd_end - anga_start, 0)
  vyapti_1 = max(anga_end - d1_angas.interval.jd_start, 0)
  return 1 if vyapti_1 > vyapti_0 else 0


def decide_vyaapti(p0, p1, target_anga, ayanaamsha_id, kaala):
  (d0_angas, d1_angas) = get_2_day_interval_boundary_angas(kaala=kaala, anga_type=target_anga.get_type(), p0=p0, p1=p1)
  # if kaala not in ['अपराह्णः']:
  #   raise ValueError(kaala)

  prev_anga = target_anga - 1
  next_anga = target_anga + 1
  p, q, r = prev_anga, target_anga, next_anga  # short-hand
  # Combinations
  # (p:0, q:1, r:2)
  # <a> r ? ? ?: None
  # <a> ? ? q q: d + 1
  # <b> ? p ? ?: d + 1
  # <e> p q q r: vyApti
  # <h> q q ? r: d
  # <i> ? q r ?: d
  # <j> q r ? ?: d
  if d0_angas.start > q:
    # One of the cases covered here: Anga might have been between end of previous day's interval and beginning of this day's interval. Then we would have: r r for d1_angas. Could potentially lead to a missed festival.
    # logging.debug("vyaapti: %s, %s, %s - Not assigning a festival this day. Likely checking on the wrong day pair.", str(d0_angas.to_tuple()), str(d1_angas.to_tuple()), str(target_anga.index))
    return None

  # Easy cases where d0 has greater vyApti
  elif d0_angas.end > q:
    # d0_angas.start <= q
    fday = 0
  elif d0_angas.start == q and d0_angas.end == q and d1_angas.end > q:
    fday = 0
  elif d0_angas.end == q and d1_angas.start > q:
    fday = 0

  # Easy cases where d1 has greater vyApti
  elif d1_angas.start == q and d1_angas.end == q:
    if d0_angas.start == q and d0_angas.end == q:
      # Both d0 and d1 fully cover the kaala -- a genuine tie (eg. an unusually long-duration anga spanning
      # both days' kaalas in full); compare true durations rather than defaulting to d1.
      fday = compare_vyaapti_duration(d0_angas=d0_angas, d1_angas=d1_angas, target_anga=target_anga, ayanaamsha_id=ayanaamsha_id)
    else:
      fday = 1
  elif d0_angas.end < q and d1_angas.start >= q:
    # Covers p p r r, [p, p, q, r], [p, p, q, q]
    fday = 1

  elif d0_angas.end == q and d1_angas.start == q:
    # The <e> p q q r: vyApti case
    fday = compare_vyaapti_duration(d0_angas=d0_angas, d1_angas=d1_angas, target_anga=target_anga, ayanaamsha_id=ayanaamsha_id)

  else:
    # logging.info("vyaapti: %s, %s, %s. Some weird case", str(d0_angas.to_tuple()), str(d1_angas.to_tuple()), str(target_anga.index))
    fday = None
  return FestivalDecision.from_details(boundary_angas_list=[d0_angas, d1_angas], fday=fday, panchaangas=[p0, p1])


def decide(p0, p1, target_anga, kaala, priority, ayanaamsha_id):
  """ Decide between p0 and p1 depending on the event parameters
  
  :param p0: 
  :param p1: 
  :param target_anga: 
  :param kaala: 
  :param priority: 
  :param ayanaamsha_id: 
  :return: FestivalDecision object.
  """
  if priority == 'paraviddha':
    decision = decide_paraviddha(p0=p0, p1=p1, target_anga=target_anga, kaala=kaala)
  elif priority == 'puurvaviddha':
    decision = decide_puurvaviddha(p0=p0, p1=p1, target_anga=target_anga, kaala=kaala)
  elif priority == 'vyaapti':
    decision = decide_vyaapti(p0=p0, p1=p1, target_anga=target_anga, kaala=kaala, ayanaamsha_id=ayanaamsha_id)
  else:
    raise ValueError('Unknown priority %s' % priority)
  return decision

