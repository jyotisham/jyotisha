import logging
import sys

from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal import PeriodicPanchaangaApplier
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.time import Hour
from sanskrit_data.schema import common

TYAJYA_SPANS_REL = [51, 25, 31, 41, 15, 22, 31, 21, 33,
                    31, 21, 19, 22, 21, 15, 15, 11, 15,
                    57, 25, 21, 11, 11, 19, 17, 25, 31]
AMRITA_SPANS_REL = [43, 49, 55, 53, 39, 36, 55, 45, 57,
                    55, 45, 43, 46, 45, 39, 39, 35, 39,
                    45, 49, 45, 35, 35, 43, 41, 49, 55]
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
  def _get_nakshatra_data(self):
    nakshatra_flat_list = []

    for dp in self.panchaanga.daily_panchaangas_sorted():
      for sublist in [dp.sunrise_day_angas.nakshatras_with_ends]:
        for item in sublist:
          if not (item.jd_start == item.jd_end == None):
            nakshatra_flat_list.append(item)

    nakshatra_data = []

    i = 0
    while nakshatra_flat_list[i].jd_start is None:
      i += 1

    while i < len(nakshatra_flat_list) - 1:
      if nakshatra_flat_list[i].jd_end is None:
        assert nakshatra_flat_list[i].anga.index == nakshatra_flat_list[i + 1].anga.index
        nakshatra_data.append((nakshatra_flat_list[i].anga.index, nakshatra_flat_list[i].jd_start, nakshatra_flat_list[i + 1].jd_end))
        i += 2
      else:
        nakshatra_data.append((nakshatra_flat_list[i].anga.index, nakshatra_flat_list[i].jd_start, nakshatra_flat_list[i].jd_end))
        i += 1

    return nakshatra_data

  def calc_nakshatra_tyaajya_amrta(self, debug=False):
    nakshatra_data = self._get_nakshatra_data()

    self.panchaanga.tyajyam_data = [[] for _x in range(self.panchaanga.duration + 2)]
    self.panchaanga.amrita_data = [[] for _x in range(self.panchaanga.duration + 2)]

    tyaajya_list = []
    amrita_list = []

    for n, t_start, t_end in nakshatra_data:
      tyaajya_start = t_start + (t_end - t_start) / 60 * (TYAJYA_SPANS_REL[n - 1] - 1)
      tyaajya_end = t_start + (t_end - t_start) / 60 * (TYAJYA_SPANS_REL[n - 1] + 3)
      tyaajya_list += [(tyaajya_start, tyaajya_end)]

      amrita_start = t_start + (t_end - t_start) / 60 * (AMRITA_SPANS_REL[n - 1] - 1)
      amrita_end = t_start + (t_end - t_start) / 60 * (AMRITA_SPANS_REL[n - 1] + 3)
      amrita_list += [(amrita_start, amrita_end)]

    j = 0
    for d in range(self.panchaanga.duration + 1):
      while self.daily_panchaangas[d].jd_sunrise < tyaajya_list[j][0] < self.daily_panchaangas[d + 1].jd_sunrise:
        self.panchaanga.tyajyam_data[d] += [tyaajya_list[j]]
        j += 1
  
    j = 0
    for d in range(self.panchaanga.duration + 1):
      while self.daily_panchaangas[d].jd_sunrise < amrita_list[j][0] < self.daily_panchaangas[d + 1].jd_sunrise:
        self.panchaanga.amrita_data[d] += [amrita_list[j]]
        j += 1
  
# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
