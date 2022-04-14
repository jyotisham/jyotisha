import logging
import sys

from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal import PeriodicPanchaangaApplier
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.time import Hour
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType
from sanskrit_data.schema import common

TYAJYA_START_REL_NAKSHATRA = [50, 24, 30, 40, 14, 21, 30, 20, 32, 30, 20, 18, 21, 20, 14, 14, 10, 14, 56, 24, 20, 10, 10, 18, 16, 24, 30]
AMRITA_START_REL_NAKSHATRA = [42, 48, 54, 52, 38, 35, 54, 44, 56, 54, 44, 42, 45, 44, 38, 38, 34, 38, 44, 48, 44, 34, 34, 42, 40, 48, 54]
TYAJYA_START_TITHI = [15, 5, 8, 7, 7, 5, 4, 8, 7, 10, 3, 13, 14, 7, 8]*2
TYAJYA_START_VASARA = [20, 2, 12, 10, 7, 5, 25]
AMRITADI_YOGA = [[None, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0, 0, 1, 1, 2, 2, 2, 0, 1, 0, 0, 2, 1, 1, 0, 0],
                 [None, 1, 1, 2, 0, 0, 1, 0, 1, 1, 2, 1, 1, 1, 1, 0, 2, 1, 1, 1, 1, 2, 0, 1, 1, 2, 1, 1],
                 [None, 1, 1, 1, 0, 1, 2, 1, 1, 1, 1, 1, 0, 1, 1, 1, 2, 1, 1, 0, 1, 1, 1, 1, 2, 2, 0, 1],
                 [None, 2, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 2, 1, 1, 1, 1, 1, 2, 0, 0, 1, 2, 1, 0, 1, 2],
                 [None, 0, 1, 2, 2, 2, 2, 0, 0, 1, 0, 1, 2, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1],
                 [None, 0, 1, 1, 2, 1, 1, 1, 2, 2, 2, 1, 1, 0, 1, 1, 1, 1, 2, 0, 1, 1, 2, 1, 1, 1, 1, 0],
                 [None, 1, 1, 0, 0, 1, 1, 1, 1, 2, 0, 1, 2, 2, 2, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 2, 1, 2]]
AMRITADI_YOGA_NAMES = {1: 'siddha', 0: 'amRta', 2: 'maraNa'}
for i in range(7):
  AMRITADI_YOGA[i] = [AMRITADI_YOGA_NAMES.get(n, n) for n in AMRITADI_YOGA[i]]


class NakshatraAssigner(PeriodicPanchaangaApplier):
  def _get_anga_data(self, anga_type):
    if anga_type == AngaType.TITHI:
      anga_name = 'tithis'
    elif anga_type == AngaType.NAKSHATRA:
      anga_name = 'nakshatras'
    elif anga_type == AngaType.YOGA:
      anga_name = 'yogas'
    elif anga_type == AngaType.KARANA:
      anga_name = 'karanas'
    elif anga_type == AngaType.RASHI:
      anga_name = 'raashis'
    elif anga_type == AngaType.SOLAR_NAKSH:
      anga_name = 'solar_nakshatras'
    else:
      raise ValueError('Unknown/unsupported AngaType %s' % anga_type)

    anga_flat_list = []

    for dp in self.panchaanga.daily_panchaangas_sorted():
      for sublist in [getattr(dp.sunrise_day_angas, anga_name + '_with_ends')]:
        for item in sublist:
          if not (item.jd_start == item.jd_end == None):
            anga_flat_list.append(item)

    anga_data = []

    i = 0
    while anga_flat_list[i].jd_start is None:
      i += 1

    while i < len(anga_flat_list) - 1:
      if anga_flat_list[i].jd_end is None:
        assert anga_flat_list[i].anga.index == anga_flat_list[i + 1].anga.index
        anga_data.append((anga_flat_list[i].anga.index, anga_flat_list[i].jd_start, anga_flat_list[i + 1].jd_end))
        i += 2
      else:
        anga_data.append((anga_flat_list[i].anga.index, anga_flat_list[i].jd_start, anga_flat_list[i].jd_end))
        i += 1

    return anga_data

  def calc_nakshatra_tyaajya_amrta(self, debug=False):
    nakshatra_data = self._get_anga_data(AngaType.NAKSHATRA)

    self.panchaanga.tyajyam_data = [{'NAKSHATRAM': [], 'VASARA': [], 'TITHI': []} for _x in range(self.panchaanga.duration + 2)]
    self.panchaanga.amrita_data = [[] for _x in range(self.panchaanga.duration + 2)]

    tyaajya_list = []
    amrita_list = []

    for n, t_start, t_end in nakshatra_data:
      tyaajya_start = t_start + (t_end - t_start) / 60 * (TYAJYA_START_REL_NAKSHATRA[n - 1])
      tyaajya_end = t_start + (t_end - t_start) / 60 * (TYAJYA_START_REL_NAKSHATRA[n - 1] + 4)
      tyaajya_list += [(tyaajya_start, tyaajya_end)]

      amrita_start = t_start + (t_end - t_start) / 60 * (AMRITA_START_REL_NAKSHATRA[n - 1])
      amrita_end = t_start + (t_end - t_start) / 60 * (AMRITA_START_REL_NAKSHATRA[n - 1] + 4)
      amrita_list += [(amrita_start, amrita_end)]

    j = 0
    for d in range(self.panchaanga.duration + 2):
      while self.daily_panchaangas[d].jd_sunrise < tyaajya_list[j][0] < self.daily_panchaangas[d + 1].jd_sunrise:
        self.panchaanga.tyajyam_data[d]['NAKSHATRAM'] += [tyaajya_list[j]]
        j += 1

    tithi_data = self._get_anga_data(AngaType.TITHI)


    tithi_tyaajya_list = []

    for n, t_start, t_end in tithi_data:
      tyaajya_start = t_start + (t_end - t_start) / 60 * (TYAJYA_START_TITHI[n - 1])
      tyaajya_end = t_start + (t_end - t_start) / 60 * (TYAJYA_START_TITHI[n - 1] + 4)
      tithi_tyaajya_list += [(tyaajya_start, tyaajya_end)]

    j = 0
    for d in range(self.panchaanga.duration + 1):
      while self.daily_panchaangas[d].jd_sunrise < tithi_tyaajya_list[j][0] < self.daily_panchaangas[d + 1].jd_sunrise:
        self.panchaanga.tyajyam_data[d]['TITHI'] += [tithi_tyaajya_list[j]]
        j += 1

    daily_panchaangas = self.panchaanga.daily_panchaangas_sorted()
    for d, daily_panchaanga in enumerate(daily_panchaangas):
      if d > self.panchaanga.duration:
        break
      t_start = daily_panchaanga.jd_sunrise
      t_end = daily_panchaanga.jd_sunset
      n = daily_panchaanga.date.get_weekday()
      tyaajya_start = t_start + (t_end - t_start) / 60 * (TYAJYA_START_VASARA[n - 1])
      tyaajya_end = t_start + (t_end - t_start) / 60 * (TYAJYA_START_VASARA[n - 1] + 4)
      self.panchaanga.tyajyam_data[d]['VASARA'] += [(tyaajya_start, tyaajya_end)]

    j = 0
    for d in range(self.panchaanga.duration + 1):
      while self.daily_panchaangas[d].jd_sunrise < amrita_list[j][0] < self.daily_panchaangas[d + 1].jd_sunrise:
        self.panchaanga.amrita_data[d] += [amrita_list[j]]
        j += 1
  
# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
