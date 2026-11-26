""" The hOlikA nirNaya: the rule of the zAstrArtha-samanvaya-sabhA (Mumbai, 29 Dec 2024, #20, as amended there), which
reconciles the nibandhas into a rule covering every case, with the Smriti Kaustubha's verses as its basis.

TOML:

  [timing]
  month_type = "lunar_month"
  month_number = 12
  anga_type = "tithi"
  anga_number = 15
  kaala = "प्रदोषः"
  nirnaya = "holikaa"

`priority` is not read; the rule below replaces it. No `nirnaya_options`.

Smriti Kaustubha p.516-518 (phAlguna-kRtyam, hOlikotsavaH), the verses the rule rests on:
- "प्रदोषव्यापिनी ग्राह्या पूर्णिमा फाल्गुनी सदा" (nArada)
- "तस्यां भद्रामुखं त्यक्त्वा पूज्या होला निशामुखे" (nArada); with the parts of bhadrA, "मुखे पञ्च गले त्वेका वक्षस्येकादश
  स्मृताः। नाभौ चतस्रः षट् श्रोणौ तिस्रः पुच्छाख्यनाडिकाः" (nArada, see bhadraa.py)
- "सार्धयामत्रयं पूर्णा द्वितीये दिवसे यदा। प्रतिपद्वर्धमाना तु तदा सा होलिका स्मृता" (bhaviSyottara, via nirNayAmRta)
- "दिनार्धात्परतोऽपि स्यात्फाल्गुनी पूर्णिमा यदि। रात्रौ भद्रावसाने च होलिकां तत्र दीपयेत्" (purANa-samuccaya); "होलां
  भद्रावसाने च निशि स्वान्ते प्रदीपयेत्" (bhaviSyottara)
- "पृथिव्यां यानि कार्याणि शुभानि त्वशुभानि च। तानि सर्वाणि सिध्यन्ति विष्टिपुच्छे न संशयः" (lalla)
- "पूर्वविद्धा प्रकर्तव्या फाल्गुनी पूर्णिमा सदा" (zivarahasya); "श्रावणी दुर्गनवमी दूर्वा चैव हुताशनी। पूर्वविद्धा प्रकर्तव्या
  शिवरात्रिर्बलेर्दिनम्" (bRhadyama)
- "दिवा भद्रा यदा रात्रौ रात्रिभद्रा यदा दिवा। सा भद्रा भद्रदा यस्माद्भद्रा कल्याणकारिणी" (jyotiHzAstra)

The rule (sabhA #20), with A the civil day on which the pUrNimA begins and B the next:
1. "दोनों दिन होने पर – पूर्णिमा दोनों दिन प्रदोषकाल में न्यूनाधिक होने पर दूसरे दिन": the pUrNimA in the kAla of both days
   -> B. (The sabhA struck its earlier "भद्रारहित" here: on B the pUrNimA is in its 2nd half, free of viSTi anyway.)
2. "दोनों दिन न होने पर - पूर्णिमा दोनों दिन प्रदोषकाल में न होने पर, दूसरे दिन": in neither -> B.
3. "केवल पूर्वदिन प्रदोषकाल में होने पर भद्रामुख को छोडकर होलिका दहन": only in A's -> A, avoiding the bhadrA-mukha. (The
   sabhA struck the "साढ़े तीन प्रहर … प्रतिपदा वृद्धिगामी" sub-rules that followed: SK's sArdhayAmatraya verse.)
   Only in B's -> B (the main rule: "प्रदोषकाल व्यापिनी").
4. "ग्रस्तोदित ग्रहण होने पर प्रदोषकाल में पूर्णिमा हो तो ग्रहणकाल में भी होलिका दहन हो सकता है, परंतु प्रदोषकाल में पूर्णिमा न
   हो तो होलिका दहन पूर्व दिन करना चाहिए" (dharmasindhu): if the day chosen has a lunar eclipse in progress at moonrise
   (grastodaya), it stands when the pUrNimA is in that day's kAla, even during the eclipse; else the day before.

The time recorded: the kAla of the chosen day; in case 3, the part of A's kAla in the pUrNimA outside the bhadrA-mukha,
else (the kAla being all mukha) from the end of the mukha, until the pUrNimA or the night ends; when case 4 moves the day back, the first time that night in
the pUrNimA outside the mukha.
"""

import logging

from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival.nirnaya import NirnayaResult, find_tithi_spans
from jyotisha.panchaanga.temporal.festival.nirnaya.bhadraa import intersect, subtract, get_avoided_intervals
from jyotisha.panchaanga.temporal.interval import Interval

COMPANION_SUFFIXES = []


def _kaala(day, kaala):
  interval = day.get_interval(interval_id=kaala)
  return (interval.jd_start, interval.jd_end)


def _interval(pair, name):
  return Interval(jd_start=pair[0], jd_end=pair[1], name=name)


def has_grastodaya_lunar_eclipse(city, day):
  """ Whether the moon rises eclipsed on `day` (a lunar eclipse in progress at that day's moonrise). """
  moonrise = city.get_rising_time(julian_day_start=day.jd_sunrise, body=Graha.MOON)
  if moonrise is None:
    return False
  eclipse = city.get_lunar_eclipse_time(day.jd_sunrise - 1)
  contact_start, contact_end = eclipse[1][2], eclipse[1][3]
  if contact_end == 0.0:
    return False
  if contact_start == 0.0:
    # Begins below the horizon, as swisseph reports it: in progress at moonrise if it ends after that moonrise.
    return day.jd_sunrise <= contact_end < day.jd_next_sunrise and contact_end > moonrise
  return contact_start <= moonrise <= contact_end


def _first_free(window, night_end, avoid):
  """ The first piece of `window` outside bhadrA-mukha; else (the window being all mukha) from the end of the mukha
  until `night_end`. """
  if window is None:
    return None, None
  free = subtract(window, get_avoided_intervals(*window, avoid=avoid))
  if free:
    return free[0], 'bhadrA-mukha-rahita'
  mukha_end = max(end for (_, end) in get_avoided_intervals(*window, avoid=avoid))
  return (mukha_end, night_end), 'bhadrA-mukha-anta'


def decide_one(assigner, fest_id, kaala, d, ts, te):
  days = assigner.daily_panchaangas
  day_a, day_b = days[d], days[d + 1]
  tithi = (ts, te)
  in_kaala_a = intersect(_kaala(day_a, kaala), tithi)
  in_kaala_b = intersect(_kaala(day_b, kaala), tithi)

  if in_kaala_a is not None and in_kaala_b is None:
    # 3: only A -> A, avoiding the bhadrA-mukha.
    pair, name = _first_free(in_kaala_a, night_end=min(te, day_a.jd_next_sunrise), avoid="mukha")
    return NirnayaResult(fest_id=fest_id, date=day_a.date, interval=_interval(pair, name))

  # 1, 2 and "only B" -> B; 4: unless B's moon rises eclipsed and the pUrNimA is not in B's kAla.
  if in_kaala_b is None and has_grastodaya_lunar_eclipse(assigner.panchaanga.city, day_b):
    night_a = intersect((_kaala(day_a, kaala)[0], day_a.jd_next_sunrise), tithi)
    pair, name = _first_free(night_a, night_end=min(te, day_a.jd_next_sunrise), avoid="mukha")
    if pair is None:
      logging.warning('%s: grastodaya eclipse on %s moves hOlikA to %s, but the pUrNimA is not in that night.', fest_id,
                      day_b.date.get_date_str(), day_a.date.get_date_str())
      return NirnayaResult(fest_id=fest_id, date=day_a.date)
    return NirnayaResult(fest_id=fest_id, date=day_a.date, interval=_interval(pair, name))
  return NirnayaResult(fest_id=fest_id, date=day_b.date, interval=_interval(_kaala(day_b, kaala), kaala))


def decide(assigner, rule):
  timing = rule.timing
  if timing.anga_type != 'tithi':
    raise ValueError('%s: the holikaa nirnaya needs anga_type = "tithi"' % rule.id)
  kaala = timing.get_kaala()
  return [decide_one(assigner=assigner, fest_id=rule.id, kaala=kaala, d=d, ts=ts, te=te)
          for (d, ts, te) in find_tithi_spans(assigner, month_number=timing.month_number, tithi_index=timing.anga_number)]
