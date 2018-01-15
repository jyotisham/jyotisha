#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import logging
import swisseph as swe
from datetime import datetime

from indic_transliteration import xsanscript as sanscript
from sanskrit_data.schema import common

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")


class DailyPanchangam(common.JsonObject):
  """This class enables the construction of a panchangam
    """

  def __init__(self, city, julian_day, script=sanscript.DEVANAGARI, fmt='hh:mm', ayanamsha_id=swe.SIDM_LAHIRI):
    """Constructor for the panchangam.
        """
    super().__init__()
    self.city = city
    self.script = script
    self.fmt = fmt
    self.julian_day = julian_day
    self.julian_day_start = self.julian_day - (self.city.get_timezone_offset_hours / 24.0)

  def compute_solar_info(self):
    self.jd_sunrise = swe.rise_trans(
      jd_start=self.julian_day_start, body=swe.SUN,
      lon=self.city.longitude, lat=self.city.latitude,
      rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]
    self.jd_sunset = swe.rise_trans(
      jd_start=self.jd_sunrise, body=swe.SUN,
      lon=self.city.longitude, lat=self.city.latitude,
      rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]
