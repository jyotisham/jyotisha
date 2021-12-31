import logging

from jyotisha.panchaanga.temporal import zodiac, get_2_day_interval_boundary_angas


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
      else:
        boundary_angas = boundary_angas_list[fday]
      return FestivalDecision(day_panchaanga=panchaangas[fday], boundary_angas=boundary_angas, fday=fday)


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
  elif d0_angas.end == target_anga:
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
      # d_offset = {'sunrise': 0, 'aparaahna': 1, 'moonrise': 0, 'madhyaahna': 1, 'sunset': 1}[kaala]
      d_offset = 0 if kaala in ['sunrise', 'moonrise'] else 1
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
    # d0_angas <= q
    # This is a potential tie-breaker where both d1 and d2 are fully covered.
    fday = 1
  elif d0_angas.end < q and d1_angas.start >= q:
    # Covers p p r r, [p, p, q, r], [p, p, q, q]
    fday = 1

  elif d0_angas.end == q and d1_angas.start == q:
    # The <e> p q q r: vyApti case
    anga_span = zodiac.AngaSpanFinder(ayanaamsha_id=ayanaamsha_id, anga_type=target_anga.get_type()).find(jd1=d0_angas.interval.jd_start, jd2=d1_angas.interval.jd_end, target_anga_id=target_anga)
    vyapti_0 = max(d0_angas.interval.jd_end - anga_span.jd_start, 0)
    vyapti_1 = max(anga_span.jd_end - d1_angas.interval.jd_start, 0)
    if vyapti_1 > vyapti_0:
      fday = 0 + 1
    else:
      fday = 0

  else:
    # logging.info("vyaapti: %s, %s, %s. Some weird case", str(d0_angas.to_tuple()), str(d1_angas.to_tuple()), str(target_anga.index))
    fday = None
  return FestivalDecision.from_details(boundary_angas_list=[d0_angas, d1_angas], fday=fday, panchaangas=[p0, p1])


def decide(p0, p1, target_anga, kaala, priority, ayanaamsha_id):
  if priority == 'paraviddha':
    decision = decide_paraviddha(p0=p0, p1=p1, target_anga=target_anga, kaala=kaala)
  elif priority == 'puurvaviddha':
    decision = decide_puurvaviddha(p0=p0, p1=p1, target_anga=target_anga, kaala=kaala)
  elif priority == 'vyaapti':
    decision = decide_vyaapti(p0=p0, p1=p1, target_anga=target_anga, kaala=kaala, ayanaamsha_id=ayanaamsha_id)
  return decision

