import logging
import os
import swisseph as swe
import sys
import traceback

from datetime import datetime
from math import floor
from typing import List

from indic_transliteration import xsanscript as sanscript
from pytz import timezone as tz
from sanskrit_data.schema.common import JsonObject

from jyotisha.panchangam import temporal, spatio_temporal
from jyotisha.panchangam.temporal.festival import read_old_festival_rules_dict
from sanskrit_data.schema import common
from scipy.optimize import brentq

import jyotisha.panchangam
import jyotisha.zodiac
from jyotisha.panchangam.spatio_temporal import CODE_ROOT, daily, CALC_RISE, CALC_SET


class Panchangam(common.JsonObject):
    """This class enables the construction of a panchangam
      """

    def __init__(self, city, year=2012, script=sanscript.DEVANAGARI, fmt='hh:mm', ayanamsha_id=swe.SIDM_LAHIRI,
                 compute_lagnams=False):
        """Constructor for the panchangam.
        :param compute_lagnams:
        :param compute_lagnams:
            """
        super(Panchangam, self).__init__()
        self.city = city
        self.year = year
        self.script = script
        self.fmt = fmt

        self.jd_start_utc = swe.julday(year, 1, 1, 0)

        self.weekday_start = swe.day_of_week(swe.julday(year, 1, 1)) + 1
        # swe has Mon = 0, non-intuitively!
        self.ayanamsha_id = ayanamsha_id
        swe.set_sid_mode(ayanamsha_id)
        self.add_details(compute_lagnams=compute_lagnams)

    def compute_angams(self, compute_lagnams=True):
        """Compute the entire panchangam
        """

        # INITIALISE VARIABLES
        self.jd_midnight = [None] * temporal.MAX_SZ
        self.jd_sunrise = [None] * temporal.MAX_SZ
        self.jd_sunset = [None] * temporal.MAX_SZ
        self.jd_moonrise = [None] * temporal.MAX_SZ
        self.jd_moonset = [None] * temporal.MAX_SZ
        self.solar_month = [None] * temporal.MAX_SZ
        self.solar_month_end_time = [None] * temporal.MAX_SZ
        self.solar_month_day = [None] * temporal.MAX_SZ

        solar_month_sunrise = [None] * temporal.MAX_SZ

        self.lunar_month = [None] * temporal.MAX_SZ
        self.tithi_data = [None] * temporal.MAX_SZ
        self.tithi_sunrise = [None] * temporal.MAX_SZ
        self.nakshatram_data = [None] * temporal.MAX_SZ
        self.nakshatram_sunrise = [None] * temporal.MAX_SZ
        self.yogam_data = [None] * temporal.MAX_SZ
        self.yogam_sunrise = [None] * temporal.MAX_SZ
        self.karanam_data = [None] * temporal.MAX_SZ
        self.rashi_data = [None] * temporal.MAX_SZ
        self.lagna_data = [None] * temporal.MAX_SZ

        self.weekday = [None] * temporal.MAX_SZ
        self.kaalas = [dict() for _x in range(temporal.MAX_SZ)]
        daily_panchaangas: List[daily.Panchangam] = [None] * temporal.MAX_SZ

        # Computing solar month details for Dec 31
        # rather than Jan 1, since we have an always increment
        # solar_month_day at the start of the loop across every day in
        # year
        daily_panchangam_start = daily.Panchangam(city=self.city, year=self.year - 1, month=12, day=31, ayanamsha_id=self.ayanamsha_id)
        daily_panchangam_start.compute_solar_day()
        self.solar_month[1] = daily_panchangam_start.solar_month
        solar_month_day = daily_panchangam_start.solar_month_day

        if self.solar_month[1] != 9:
            logging.error(self.solar_month[1])
            raise (ValueError('Dec 31 does not appear to be Dhanurmasa!'))

        month_start_after_sunset = False

        #############################################################
        # Compute all parameters -- sun/moon latitude/longitude etc #
        #############################################################

        for d in range(temporal.MAX_SZ):
            self.weekday[d] = (self.weekday_start + d - 1) % 7

        for d in range(-1, temporal.MAX_DAYS_PER_YEAR + 4):
            # TODO: Eventually, we are shifting to an array of daily panchangas. Reason: Better modularity.
            # The below block is temporary code to make the transition seamless.
            (year_d, month_d, day_d, _) = swe.revjul(self.jd_start_utc + d)
            daily_panchaangas[d + 1] = daily.Panchangam(city=self.city, year=year_d, month=month_d, day=day_d, ayanamsha_id=self.ayanamsha_id, previous_day_panchangam=daily_panchaangas[d])
            daily_panchaangas[d + 1].compute_sun_moon_transitions(previous_day_panchangam=daily_panchaangas[d])
            daily_panchaangas[d + 1].compute_solar_month()
            self.jd_midnight[d + 1] = daily_panchaangas[d + 1].julian_day_start
            self.jd_sunrise[d + 1] = daily_panchaangas[d + 1].jd_sunrise
            self.jd_sunset[d + 1] = daily_panchaangas[d + 1].jd_sunset
            self.jd_moonrise[d + 1] = daily_panchaangas[d + 1].jd_moonrise
            self.jd_moonset[d + 1] = daily_panchaangas[d + 1].jd_moonset
            self.solar_month[d + 1] = daily_panchaangas[d + 1].solar_month_sunset

            solar_month_sunrise[d + 1] = daily_panchaangas[d + 1].solar_month_sunrise

            if (d <= 0):
                continue
                # This is just to initialise, since for a lot of calculations,
                # we require comparing with tomorrow's data. This computes the
                # data for day 0, -1.

            # Solar month calculations
            if month_start_after_sunset is True:
                solar_month_day = 0
                month_start_after_sunset = False

            solar_month_end_jd = None
            if self.solar_month[d] != self.solar_month[d + 1]:
                solar_month_day = solar_month_day + 1
                if self.solar_month[d] != solar_month_sunrise[d + 1]:
                    month_start_after_sunset = True
                    [_m, solar_month_end_jd] = temporal.get_angam_data(
                        self.jd_sunrise[d], self.jd_sunrise[d + 1], temporal.SOLAR_MONTH,
                        ayanamsha_id=self.ayanamsha_id)[0]
            elif solar_month_sunrise[d] != self.solar_month[d]:
                # sankrAnti!
                # sun moves into next rAshi before sunset
                solar_month_day = 1
                [_m, solar_month_end_jd] = temporal.get_angam_data(
                    self.jd_sunrise[d], self.jd_sunrise[d + 1], temporal.SOLAR_MONTH,
                    ayanamsha_id=self.ayanamsha_id)[0]
            else:
                solar_month_day = solar_month_day + 1
                solar_month_end_jd = None

            # if self.solar_month[d-1] != self.solar_month[d]:
            #     # We have a sUrya sankrAnti between yest. and today's sunsets
            #     solar_month_day = 1
            #     if solar_month_sunrise[d] == self.solar_month[d]:
            #         #the sankrAnti happened before today's sunrise
            #         #so search for the end time between yesterday and
            #         #today's sunrises
            #         [_m, solar_month_end_jd] = helper_functions.get_angam_data(self.jd_sunrise[d-1],
            #             self.jd_sunrise[d],SOLAR_MONTH)[0]
            #     else:
            #         #the sankrAnti happens after today's sunrise
            #         #so search for the end time between today and
            #         #tomorrow's sunrises
            #         [_m, solar_month_end_jd] = helper_functions.get_angam_data(self.jd_sunrise[d],
            #             self.jd_sunrise[d + 1],SOLAR_MONTH)[0]
            #     #print ('-----',revjul(jd = solar_month_end_jd, tz_off = tz_off))
            # else:
            #     solar_month_day += 1
            #     solar_month_end_jd = None

            self.solar_month_end_time[d] = solar_month_end_jd

            self.solar_month_day[d] = solar_month_day

            self.kaalas[d] = daily_panchaangas[d].get_kaalas()

            # Compute all the anga datas
            self.tithi_data[d] = daily_panchaangas[d].tithi_data
            self.tithi_sunrise[d] = daily_panchaangas[d].tithi_at_sunrise
            self.nakshatram_data[d] = daily_panchaangas[d].nakshatram_data
            self.nakshatram_sunrise[d] = daily_panchaangas[d].nakshatram_at_sunrise
            self.yogam_data[d] = daily_panchaangas[d].yogam_data
            self.yogam_sunrise[d] = daily_panchaangas[d].yogam_at_sunrise
            self.karanam_data[d] = daily_panchaangas[d].karanam_data
            self.rashi_data[d] = daily_panchaangas[d].rashi_data
            if compute_lagnams:
                self.lagna_data[d] = daily_panchaangas[d].get_lagna_data(self.jd_sunrise[d])

    def assignLunarMonths(self):
        last_d_assigned = 0
        last_new_moon_start, last_new_moon_end = temporal.get_angam_span(
            self.jd_start_utc - self.tithi_sunrise[1] - 2, self.jd_start_utc - self.tithi_sunrise[1] + 2, temporal.TITHI, 30, ayanamsha_id=self.ayanamsha_id)
        this_new_moon_start, this_new_moon_end = temporal.get_angam_span(last_new_moon_start + 24, last_new_moon_start + 32, temporal.TITHI, 30, ayanamsha_id=self.ayanamsha_id)
        # Check if current mAsa is adhika here
        isAdhika = temporal.get_solar_rashi(last_new_moon_end, ayanamsha_id=self.ayanamsha_id) == \
                   temporal.get_solar_rashi(this_new_moon_end, ayanamsha_id=self.ayanamsha_id)

        while last_new_moon_start < self.jd_start_utc + 367:
            next_new_moon_start, next_new_moon_end = temporal.get_angam_span(this_new_moon_start + 24, this_new_moon_start + 32, temporal.TITHI, 30, ayanamsha_id=self.ayanamsha_id)
            for i in range(last_d_assigned + 1, last_d_assigned + 32):
                last_solar_month = temporal.get_solar_rashi(this_new_moon_end, ayanamsha_id=self.ayanamsha_id)

                if i > 367 or self.jd_sunrise[i] > this_new_moon_end:
                    last_d_assigned = i - 1
                    break
                if isAdhika:
                    self.lunar_month[i] = (last_solar_month % 12) + .5
                else:
                    self.lunar_month[i] = last_solar_month

            isAdhika = temporal.get_solar_rashi(this_new_moon_end, ayanamsha_id=self.ayanamsha_id) == \
                       temporal.get_solar_rashi(next_new_moon_end, ayanamsha_id=self.ayanamsha_id)
            last_new_moon_start = this_new_moon_start
            last_new_moon_end = this_new_moon_end
            this_new_moon_start = next_new_moon_start
            this_new_moon_end = next_new_moon_end

    def get_angams_for_kaalas(self, d, get_angam_func, kaala_type):
        jd_sunrise = self.jd_sunrise[d]
        jd_sunrise_tmrw = self.jd_sunrise[d + 1]
        jd_sunrise_datmrw = self.jd_sunrise[d + 2]
        jd_sunset = self.jd_sunset[d]
        jd_sunset_tmrw = self.jd_sunset[d + 1]
        jd_moonrise = self.jd_moonrise[d]
        jd_moonrise_tmrw = self.jd_moonrise[d + 1]
        if kaala_type == 'sunrise':
            angams = [get_angam_func(jd_sunrise, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunrise, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunrise_tmrw, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunrise_tmrw, ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'sunset':
            angams = [get_angam_func(jd_sunset, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunset, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunset_tmrw, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunset_tmrw, ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'praatah':
            angams = [get_angam_func(jd_sunrise, ayanamsha_id=self.ayanamsha_id),  # praatah1 start
                      # praatah1 end
                      get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0),
                                     ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunrise_tmrw, ayanamsha_id=self.ayanamsha_id),  # praatah2 start
                      # praatah2 end
                      get_angam_func(jd_sunrise_tmrw + \
                                     (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'sangava':
            angams = [
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw +
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw +
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'madhyaahna':
            angams = [
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw +
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw + (jd_sunset_tmrw -
                                                  jd_sunrise_tmrw) * (3.0 / 5.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'aparaahna':
            angams = [
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw +
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (3.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw +
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'saayaahna':
            angams = [
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (5.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw +
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunrise_tmrw +
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (5.0 / 5.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'madhyaraatri':
            angams = [
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (2.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (3.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (2.0 / 5.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (3.0 / 5.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'pradosha':
            # pradOSo.astamayAdUrdhvaM ghaTikAdvayamiShyatE (tithyAdi tattvam, Vrat Parichay p. 25 Gita Press)
            angams = [get_angam_func(jd_sunset, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (1.0 / 15.0),
                                     ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunset_tmrw, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_sunset_tmrw +
                                     (jd_sunrise_datmrw - jd_sunset_tmrw) * (1.0 / 15.0),
                                     ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'nishita':
            angams = [
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (7.0 / 15.0),
                               ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (8.0 / 15.0),
                               ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (7.0 / 15.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (8.0 / 15.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'raatrimaana':
            angams = [
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (0.0 / 15.0),
                               ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0),
                               ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (0.0 / 15.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'arunodaya':  # deliberately not simplifying expressions involving 15/15
            angams = [
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (13.0 / 15.0),
                               ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0),
                               ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (13.0 / 15.0), ayanamsha_id=self.ayanamsha_id),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0), ayanamsha_id=self.ayanamsha_id)]
        elif kaala_type == 'moonrise':
            angams = [get_angam_func(jd_moonrise, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_moonrise, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_moonrise_tmrw, ayanamsha_id=self.ayanamsha_id),
                      get_angam_func(jd_moonrise_tmrw, ayanamsha_id=self.ayanamsha_id)]
        else:
            # Error!
            raise ValueError('Unkown kaala "%s" input!' % kaala_type)
        return angams

    def add_festival(self, festival_name, d, debug=False):
        if debug:
            logging.debug('%03d: %s ' % (d, festival_name))
        if festival_name in self.fest_days:
            if d not in self.fest_days[festival_name]:
                # Second occurrence of a festival within a
                # Gregorian calendar year
                if (d - 1) in self.fest_days[festival_name]:
                    # No festival occurs on consecutive days; paraviddha assigned twice
                    self.fest_days[festival_name].remove(d - 1)
                self.fest_days[festival_name].append(d)
        else:
            self.fest_days[festival_name] = [d]

    def compute_festivals(self):
        debug_festivals = False

        for d in range(1, temporal.MAX_DAYS_PER_YEAR + 1):
            [y, m, dt, t] = swe.revjul(self.jd_start_utc + d - 1)

            # checking @ 6am local - can we do any better?
            local_time = tz(self.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
            # compute offset from UTC in hours
            tz_off = (datetime.utcoffset(local_time).days * 86400 +
                      datetime.utcoffset(local_time).seconds) / 3600.0

            # What is the jd at 00:00 local time today?
            # jd = self.jd_start - (tz_off / 24.0) + d - 1

            ####################
            # Festival details #
            ####################

            # KARADAIYAN NOMBU
            if self.solar_month[d] == 12 and self.solar_month_day[d] == 1:
                if temporal.get_solar_rashi(self.jd_sunrise[d] - (1 / 15.0) * (self.jd_sunrise[d] - self.jd_sunrise[d - 1])) == 12:
                    # If kumbha prevails two ghatikAs before sunrise, nombu can be done in the early morning itself, else, previous night.
                    self.fest_days['ta:kAraDaiyAn2 nOn2bu'] = [d - 1]
                else:
                    self.fest_days['ta:kAraDaiyAn2 nOn2bu'] = [d]

            # --- MONTHLY VRATAMS --- #

            # EKADASHI Vratam
            # One of two consecutive tithis must appear @ sunrise!

            if (self.tithi_sunrise[d] % 15) == 10 or (self.tithi_sunrise[d] % 15) == 11:
                yati_ekadashi_fday = smaarta_ekadashi_fday = vaishnava_ekadashi_fday = None
                ekadashi_tithi_days = [x % 15 for x in self.tithi_sunrise[d:d + 3]]
                if self.tithi_sunrise[d] > 15:
                    ekadashi_paksha = 'krishna'
                else:
                    ekadashi_paksha = 'shukla'
                if ekadashi_tithi_days in [[10, 11, 12], [11, 11, 12], [10, 12, 12]]:
                    smaarta_ekadashi_fday = d + 1
                    tithi_arunodayam = temporal.get_tithi(self.jd_sunrise[d + 1] - (1 / 15.0) * (self.jd_sunrise[d + 1] - self.jd_sunrise[d]), ayanamsha_id=self.ayanamsha_id)
                    if tithi_arunodayam == 10:
                        vaishnava_ekadashi_fday = d + 2
                    else:
                        vaishnava_ekadashi_fday = d + 1
                elif ekadashi_tithi_days in [[10, 12, 13], [11, 12, 13], [11, 12, 12]]:
                    smaarta_ekadashi_fday = d
                    tithi_arunodayam = temporal.get_tithi(self.jd_sunrise[d] - (1 / 15.0) * (self.jd_sunrise[d] - self.jd_sunrise[d - 1]), ayanamsha_id=self.ayanamsha_id)
                    if tithi_arunodayam == 10:
                        vaishnava_ekadashi_fday = d + 1
                    else:
                        vaishnava_ekadashi_fday = d
                elif ekadashi_tithi_days in [[10, 11, 13], [11, 11, 13]]:
                    smaarta_ekadashi_fday = d
                    vaishnava_ekadashi_fday = d + 1
                    yati_ekadashi_fday = d + 1

                if yati_ekadashi_fday == smaarta_ekadashi_fday == vaishnava_ekadashi_fday is None:
                    # Must have already assigned
                    pass
                elif yati_ekadashi_fday is None:
                    if smaarta_ekadashi_fday == vaishnava_ekadashi_fday:
                        # It's sarva ekadashi
                        self.add_festival('sarva-' + temporal.get_ekadashi_name(ekadashi_paksha, self.lunar_month[d]), smaarta_ekadashi_fday, debug_festivals)
                        if ekadashi_paksha == 'shukla':
                            if self.solar_month[d] == 9:
                                self.add_festival('sarva-vaikuNTha-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
                    else:
                        self.add_festival('smArta-' + temporal.get_ekadashi_name(ekadashi_paksha, self.lunar_month[d]), smaarta_ekadashi_fday, debug_festivals)
                        self.add_festival('vaiSNava-' + temporal.get_ekadashi_name(ekadashi_paksha, self.lunar_month[d]), vaishnava_ekadashi_fday, debug_festivals)
                        if ekadashi_paksha == 'shukla':
                            if self.solar_month[d] == 9:
                                self.add_festival('smArta-vaikuNTha-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
                                self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)
                else:
                    self.add_festival('smArta-' + temporal.get_ekadashi_name(ekadashi_paksha, self.lunar_month[d]) + ' (gRhastha)', smaarta_ekadashi_fday, debug_festivals)
                    self.add_festival('smArta-' + temporal.get_ekadashi_name(ekadashi_paksha, self.lunar_month[d]) + ' (sannyastha)', yati_ekadashi_fday, debug_festivals)
                    self.add_festival('vaiSNava-' + temporal.get_ekadashi_name(ekadashi_paksha, self.lunar_month[d]), vaishnava_ekadashi_fday, debug_festivals)
                    if self.solar_month[d] == 9:
                        if ekadashi_paksha == 'shukla':
                            self.add_festival('smArta-vaikuNTha-EkAdazI (gRhastha)', smaarta_ekadashi_fday, debug_festivals)
                            self.add_festival('smArta-vaikuNTha-EkAdazI (sannyastha)', yati_ekadashi_fday, debug_festivals)
                            self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)

                if yati_ekadashi_fday == smaarta_ekadashi_fday == vaishnava_ekadashi_fday is None:
                    # Must have already assigned
                    pass
                else:
                    if self.solar_month[d] == 8 and ekadashi_paksha == 'shukla':
                            # self.add_festival('guruvAyupura-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
                            self.add_festival('guruvAyupura-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)
                            self.add_festival('kaizika-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)

                    # Harivasara Computation
                    if ekadashi_paksha == 'shukla':
                        harivasara_end = brentq(temporal.get_angam_float, self.jd_sunrise[smaarta_ekadashi_fday] - 2, self.jd_sunrise[smaarta_ekadashi_fday] + 2, args=(temporal.TITHI_PADA, -45, self.ayanamsha_id, False))
                    else:
                        harivasara_end = brentq(temporal.get_angam_float, self.jd_sunrise[smaarta_ekadashi_fday] - 2, self.jd_sunrise[smaarta_ekadashi_fday] + 2, args=(temporal.TITHI_PADA, -105, self.ayanamsha_id, False))
                    [_y, _m, _d, _t] = swe.revjul(harivasara_end + (tz_off / 24.0))
                    hariv_end_time = temporal.Time(swe.revjul(harivasara_end + (tz_off / 24.0))[3]).toString()
                    fday_hv = swe.julday(_y, _m, _d, 0) - self.jd_start_utc + 1
                    self.festivals[int(fday_hv)].append('harivAsaraH\\textsf{%s}{\\RIGHTarrow}\\textsf{%s}' % ('', hariv_end_time))

            # PRADOSHA Vratam
            pref = ''
            if self.tithi_sunrise[d] == 12 or self.tithi_sunrise[d] == 13:
                tithi_sunset = temporal.get_tithi(self.jd_sunset[d], ayanamsha_id=self.ayanamsha_id)
                tithi_sunset_tmrw = temporal.get_tithi(self.jd_sunset[d + 1],
                                                       ayanamsha_id=self.ayanamsha_id)
                if tithi_sunset <= 13 and tithi_sunset_tmrw != 13:
                    if self.weekday[d] == 1:
                        pref = 'sOma-'
                    elif self.weekday[d] == 6:
                        pref = 'zani-'
                    self.festivals[d].append(pref + 'pradOSa-vratam')
                elif tithi_sunset_tmrw == 13:
                    if self.weekday[d + 1] == 1:
                        pref = 'sOma-'
                    elif self.weekday[d + 1] == 6:
                        pref = 'zani-'
                    self.festivals[d + 1].append(pref + 'pradOSa-vratam')

            if self.tithi_sunrise[d] == 27 or self.tithi_sunrise[d] == 28:
                tithi_sunset = temporal.get_tithi(self.jd_sunset[d], ayanamsha_id=self.ayanamsha_id)
                tithi_sunset_tmrw = temporal.get_tithi(self.jd_sunset[d + 1],
                                                       ayanamsha_id=self.ayanamsha_id)
                if tithi_sunset <= 28 and tithi_sunset_tmrw != 28:
                    if self.weekday[d] == 1:
                        pref = 'sOma-'
                    elif self.weekday[d] == 6:
                        pref = 'zani-'
                    self.festivals[d].append(pref + 'pradOSa-vratam')
                elif tithi_sunset_tmrw == 28:
                    if self.weekday[d + 1] == 1:
                        pref = 'sOma-'
                    elif self.weekday[d + 1] == 6:
                        pref = 'zani-'
                    self.festivals[d + 1].append(pref + 'pradOSa-vratam')

            # SANKATAHARA chaturthi
            if self.tithi_sunrise[d] == 18 or self.tithi_sunrise[d] == 19:
                ldiff_moonrise_yest = (swe.calc_ut(self.jd_moonrise[d - 1], swe.MOON)[0] -
                                       swe.calc_ut(self.jd_moonrise[d - 1], swe.SUN)[0]) % 360
                ldiff_moonrise = (swe.calc_ut(self.jd_moonrise[d], swe.MOON)[0] -
                                  swe.calc_ut(self.jd_moonrise[d], swe.SUN)[0]) % 360
                ldiff_moonrise_tmrw = (swe.calc_ut(self.jd_moonrise[d + 1], swe.MOON)[0] -
                                       swe.calc_ut(self.jd_moonrise[d + 1], swe.SUN)[0]) % 360
                tithi_moonrise_yest = int(1 + floor(ldiff_moonrise_yest / 12.0))
                tithi_moonrise = int(1 + floor(ldiff_moonrise / 12.0))
                tithi_moonrise_tmrw = int(1 + floor(ldiff_moonrise_tmrw / 12.0))

                _m = self.lunar_month[d]
                if floor(_m) != _m:
                    _m = 13  # Adhika masa
                chaturthi_name = temporal.NAMES['SANKATAHARA_CHATURTHI_NAMES']['hk'][_m]
                chaturthi_name += '-mahAgaNapati '
                if self.weekday[d] == 2:
                    chaturthi_name = 'aGgArakI~' + chaturthi_name

                if tithi_moonrise == 19:
                    # otherwise yesterday would have already been assigned
                    if tithi_moonrise_yest != 19:
                        self.festivals[d].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
                        # shravana krishna chaturthi
                        if self.lunar_month[d] == 5:
                            self.festivals[d][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'
                elif tithi_moonrise_tmrw == 19:
                    self.festivals[d + 1].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
                    # self.lunar_month[d] and[d + 1] are same, so checking [d] is enough
                    if self.lunar_month[d] == 5:
                        self.festivals[d + 1][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'
                else:
                    if tithi_moonrise_yest != 19:
                        if tithi_moonrise == 18 and tithi_moonrise_tmrw == 20:
                            self.festivals[d].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
                            # shravana krishna chaturthi
                            if self.lunar_month[d] == 5:
                                self.festivals[d][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'

            # # SHASHTHI Vratam
            # Check only for Adhika maasa here...
            festival_name = 'SaSThI-vratam'
            if self.lunar_month[d] == 8:
                festival_name = 'skanda' + festival_name
            elif self.lunar_month[d] == 4:
                festival_name = 'kumAra-' + festival_name
            elif self.lunar_month[d] == 6:
                festival_name = 'SaSThIdEvI-' + festival_name
            elif self.lunar_month[d] == 9:
                festival_name = 'subrahmaNya-' + festival_name

            if self.tithi_sunrise[d] == 5 or self.tithi_sunrise[d] == 6:
                angams = self.get_angams_for_kaalas(d, temporal.get_tithi, 'madhyaahna')
                if angams[0] == 6 or angams[1] == 6:
                    if festival_name in self.fest_days:
                        # Check if yesterday was assigned already
                        # to this puurvaviddha festival!
                        if self.fest_days[festival_name].count(d - 1) == 0:
                            self.add_festival(festival_name, d, debug_festivals)
                    else:
                        self.add_festival(festival_name, d, debug_festivals)
                elif angams[2] == 6 or angams[3] == 6:
                    self.add_festival(festival_name, d + 1, debug_festivals)
                else:
                    # This means that the correct angam did not
                    # touch the kaala on either day!
                    # sys.stderr.write('Could not assign puurvaviddha day for %s!\
                    # Please check for unusual cases.\n' % festival_name)
                    if angams[2] == 6 + 1 or angams[3] == 6 + 1:
                        # Need to assign a day to the festival here
                        # since the angam did not touch kaala on either day
                        # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
                        # THIS BEING PURVAVIDDHA
                        # Perhaps just need better checking of
                        # conditions instead of this fix
                        if festival_name in self.fest_days:
                            if self.fest_days[festival_name].count(d - 1) == 0:
                                self.add_festival(festival_name, d, debug_festivals)
                        else:
                            self.add_festival(festival_name, d, debug_festivals)

            # Chandra Darshanam
            if self.tithi_sunrise[d] == 1 or self.tithi_sunrise[d] == 2:
                tithi_sunset = temporal.get_tithi(self.jd_sunset[d], ayanamsha_id=self.ayanamsha_id)
                tithi_sunset_tmrw = temporal.get_tithi(self.jd_sunset[d + 1],
                                                       ayanamsha_id=self.ayanamsha_id)
                if tithi_sunset <= 2 and tithi_sunset_tmrw != 2:
                    if tithi_sunset == 1:
                        self.festivals[d + 1].append('candra-darzanam')
                    else:
                        self.festivals[d].append('candra-darzanam')
                elif tithi_sunset_tmrw == 2:
                    self.festivals[d + 1].append('candra-darzanam')

            # Amavasya Tarpanam
            if d == 1 or self.tithi_sunrise[d] == 1 or self.tithi_sunrise[d] == 2:
                # Reset (at start) every month, as one of these two tithis must hit sunrise!
                t29_end = None
                t30_end = None
            if self.tithi_sunrise[d] == 29 or self.tithi_sunrise[d] == 30:
                if self.tithi_sunrise[d] == 29:
                    t29, t29_end = temporal.get_angam_data(
                        self.jd_sunrise[d], self.jd_sunrise[d + 1], temporal.TITHI,
                        ayanamsha_id=self.ayanamsha_id)[0]
                    t30, t30_end = temporal.get_angam_data(
                        self.jd_sunrise[d + 1], self.jd_sunrise[d + 2], temporal.TITHI,
                        ayanamsha_id=self.ayanamsha_id)[0]
                    if t30 != 30:
                        # Only 29 ends tomorrow!
                        t30, t30_end = temporal.get_angam_data(
                            self.jd_sunrise[d + 1] + 0.5,
                            self.jd_sunrise[d + 2] + 0.5, temporal.TITHI, ayanamsha_id=self.ayanamsha_id)[0]
                elif self.tithi_sunrise[d] == 30:
                    if t29_end is None:
                        # 29 never touched sunrise
                        t30, t30_end = temporal.get_angam_data(
                            self.jd_sunrise[d], self.jd_sunrise[d + 1], temporal.TITHI,
                            ayanamsha_id=self.ayanamsha_id)[0]
                        t29, t29_end = temporal.get_angam_data(t30_end - 1.5, t30_end - 0.5,
                                                               temporal.TITHI,
                                                               ayanamsha_id=self.ayanamsha_id)[0]
                # if t29_end is None:
                #   # Should never be here!
                #   sys.stderr.write('Error! Still not computed t29_end!')

                angams = self.get_angams_for_kaalas(d, temporal.get_tithi, 'aparaahna')

                # Get Name
                if self.lunar_month[d] == 6:
                    pref = '(%s) mahAlaya ' % (temporal.get_chandra_masa(self.lunar_month[d], temporal.NAMES, 'hk', visarga=False))
                elif self.solar_month[d] == 4:
                    pref = '%s (kaTaka) ' % (temporal.get_chandra_masa(self.lunar_month[d], temporal.NAMES, 'hk', visarga=False))
                elif self.solar_month[d] == 10:
                    pref = 'mauni (%s/makara) ' % (temporal.get_chandra_masa(self.lunar_month[d], temporal.NAMES, 'hk', visarga=False))
                else:
                    pref = temporal.get_chandra_masa(self.lunar_month[d], temporal.NAMES, 'hk', visarga=False) + '-'

                ama_nakshatram_today = self.get_angams_for_kaalas(d, temporal.get_nakshatram, 'aparaahna')[:2]
                ama_nakshatram_tmrw = self.get_angams_for_kaalas(d + 1, temporal.get_nakshatram, 'aparaahna')[:2]
                suff = ''
                # Assign
                if angams[0] == 30 or angams[1] == 30:
                    if angams[2] == 30 or angams[3] == 30:
                        # Amavasya is there on both aparaahnas
                        if t30_end - t29_end < 1:
                            # But not longer than 60 ghatikas
                            if 23 in ama_nakshatram_today and self.lunar_month[d] == 10:
                                suff = ' (alabhyam–zraviSThA)'
                            elif 24 in ama_nakshatram_today and self.lunar_month[d] == 10:
                                suff = ' (alabhyam–zatabhiSak)'
                            elif ama_nakshatram_today[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                                suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[0]]
                            elif ama_nakshatram_today[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                                suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[1]]
                            self.add_festival(pref + 'amAvasyA' + suff, d, debug_festivals)
                        else:
                            # And longer than 60 ghatikas
                            if 23 in ama_nakshatram_tmrw and self.lunar_month[d] == 10:
                                suff = ' (alabhyam–zraviSThA)'
                            elif 24 in ama_nakshatram_tmrw and self.lunar_month[d] == 10:
                                suff = ' (alabhyam–zatabhiSak)'
                            elif ama_nakshatram_tmrw[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                                suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_tmrw[0]]
                            elif ama_nakshatram_tmrw[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                                suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_tmrw[1]]
                            self.add_festival(pref + 'amAvasyA' + suff, d + 1, debug_festivals)
                    else:
                        # No Amavasya in aparaahna tomorrow, so it's today
                        if 23 in ama_nakshatram_today and self.lunar_month[d] == 10:
                            suff = ' (alabhyam–zraviSThA)'
                        elif 24 in ama_nakshatram_today and self.lunar_month[d] == 10:
                            suff = ' (alabhyam–zatabhiSak)'
                        elif ama_nakshatram_today[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                            suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[0]]
                        elif ama_nakshatram_today[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                            suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[1]]
                        self.add_festival(pref + 'amAvasyA' + suff, d, debug_festivals)
                else:
                    if angams == [29, 29, 1, 1]:
                        logging.warning('amAvasyA did not touch aparAhna on either day?')
                        if 23 in ama_nakshatram_tmrw and self.lunar_month[d] == 10:
                            suff = ' (alabhyam–zraviSThA)'
                        elif 24 in ama_nakshatram_tmrw and self.lunar_month[d] == 10:
                            suff = ' (alabhyam–zatabhiSak)'
                        elif ama_nakshatram_tmrw[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                            suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_tmrw[0]]
                        elif ama_nakshatram_tmrw[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
                            suff = ' (alabhyam–%s)' % jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_tmrw[1]]
                        self.add_festival(pref + 'amAvasyA' + suff, d + 1, debug_festivals)
                    # else:
                    #   logging.debug('amAvasyA must have been assigned already?')

            # MAKARAYANAM
            if self.solar_month[d] == 9 and self.solar_month_day[d] == 1:
                makara_jd_start = brentq(jyotisha.zodiac.get_nirayana_sun_lon, self.jd_sunrise[d],
                                         self.jd_sunrise[d] + 15, args=(-270, False))

            if self.solar_month[d] == 9 and 3 < self.solar_month_day[d] < 10:
                if self.jd_sunset[d] < makara_jd_start < self.jd_sunset[d + 1]:
                    self.fest_days['makarAyaNa-puNyakAlaH/mitrOtsavaH'] = [d + 1]

            # NIRAYANA AYANAMS
            if self.solar_month_day[d] == 1:
                ayana_jd_start = brentq(jyotisha.zodiac.get_nirayana_sun_lon, self.jd_sunrise[d],
                                        self.jd_sunrise[d] + 15, args=(-30 * self.solar_month[d], False))
                [_y, _m, _d, _t] = swe.revjul(ayana_jd_start + (tz_off / 24.0))
                ayana_time = temporal.Time(swe.revjul(ayana_jd_start + (tz_off / 24.0))[3]).toString()
                fday_nirayana = swe.julday(_y, _m, _d, 0) - self.jd_start_utc + 1
                self.festivals[int(fday_nirayana)].append('%s\\textsf{%s}{\\RIGHTarrow}\\textsf{%s}' % (
                    temporal.NAMES['NIRAYANA_NAMES'][self.script][self.solar_month[d]], '', ayana_time))

            # KUCHELA DINAM
            if self.solar_month[d] == 9 and self.solar_month_day[d] <= 7 and self.weekday[d] == 3:
                self.fest_days['kucEla-dinam'] = [d]

            # AGNI NAKSHATRAM
            # Arbitrarily checking after Mesha 10! Agni Nakshatram can't start earlier...
            if self.solar_month[d] == 1 and self.solar_month_day[d] == 10:
                agni_jd_start, dummy = temporal.get_angam_span(
                    self.jd_sunrise[d], self.jd_sunrise[d] + 30,
                    {'arc_len': 360.0 / 108.0, 'w_moon': 0, 'w_sun': 1}, 7, ayanamsha_id=self.ayanamsha_id)
                # sys.stderr.write('Agni Start: %s\n' % revjul(agni_jd_start + (5.5 / 24.0)))
                dummy, agni_jd_end = temporal.get_angam_span(
                    agni_jd_start, agni_jd_start + 30,
                    {'arc_len': 360.0 / 108.0, 'w_moon': 0, 'w_sun': 1}, 13, ayanamsha_id=self.ayanamsha_id)
                # sys.stderr.write('Agni End: %s\n' % revjul(agni_jd_end + (5.5 / 24.0)))

            if self.solar_month[d] == 1 and self.solar_month_day[d] > 10:
                if self.jd_sunset[d] < agni_jd_start < self.jd_sunset[d + 1]:
                    self.fest_days['agninakSatra-ArambhaH'] = [d + 1]
            if self.solar_month[d] == 2 and self.solar_month_day[d] > 10:
                if self.jd_sunset[d] < agni_jd_end < self.jd_sunset[d + 1]:
                    self.fest_days['agninakSatra-samApanam'] = [d + 1]

            # GAJACHHAYA YOGA
            if self.solar_month[d] == 6 and self.solar_month_day[d] == 1:
                moon_magha_jd_start = moon_magha_jd_start = t28_start = None
                moon_magha_jd_end = moon_magha_jd_end = t28_end = None
                moon_hasta_jd_start = moon_hasta_jd_start = t30_start = None
                moon_hasta_jd_end = moon_hasta_jd_end = t30_end = None

                sun_hasta_jd_start, sun_hasta_jd_end = temporal.get_angam_span(
                    self.jd_sunrise[d], self.jd_sunrise[d] + 30, temporal.SOLAR_NAKSH, 13,
                    ayanamsha_id=self.ayanamsha_id)

                moon_magha_jd_start, moon_magha_jd_end = temporal.get_angam_span(
                    sun_hasta_jd_start - 1, sun_hasta_jd_end + 1, temporal.NAKSHATRAM, 10,
                    ayanamsha_id=self.ayanamsha_id)
                if all([moon_magha_jd_start, moon_magha_jd_end]):
                    t28_start, t28_end = temporal.get_angam_span(
                        moon_magha_jd_start - 3, moon_magha_jd_end + 3, temporal.TITHI, 28,
                        ayanamsha_id=self.ayanamsha_id)

                moon_hasta_jd_start, moon_hasta_jd_end = temporal.get_angam_span(
                    sun_hasta_jd_start - 1, sun_hasta_jd_end + 1, temporal.NAKSHATRAM, 13,
                    ayanamsha_id=self.ayanamsha_id)
                if all([moon_hasta_jd_start, moon_hasta_jd_end]):
                    t30_start, t30_end = temporal.get_angam_span(
                        sun_hasta_jd_start - 1, sun_hasta_jd_end + 1, temporal.TITHI, 30,
                        ayanamsha_id=self.ayanamsha_id)

                gc_28 = gc_30 = False

                if all([sun_hasta_jd_start, moon_magha_jd_start, t28_start]):
                    # We have a GC yoga
                    gc_28_start = max(sun_hasta_jd_start, moon_magha_jd_start, t28_start)
                    gc_28_end = min(sun_hasta_jd_end, moon_magha_jd_end, t28_end)

                    if gc_28_start < gc_28_end:
                        gc_28 = True

                if all([sun_hasta_jd_start, moon_hasta_jd_start, t30_start]):
                    # We have a GC yoga
                    gc_30_start = max(sun_hasta_jd_start, moon_hasta_jd_start, t30_start)
                    gc_30_end = min(sun_hasta_jd_end, moon_hasta_jd_end, t30_end)

                    if gc_30_start < gc_30_end:
                        gc_30 = True

            if self.solar_month[d] == 6 and (gc_28 or gc_30):
                if gc_28:
                    gc_28_start += tz_off / 24.0
                    gc_28_end += tz_off / 24.0
                    # sys.stderr.write('28: (%f, %f)\n' % (gc_28_start, gc_28_end))
                    gc_28_d = 1 + floor(gc_28_start - self.jd_start_utc)
                    t1 = temporal.Time(swe.revjul(gc_28_start)[3]).toString()

                    if floor(gc_28_end - 0.5) != floor(gc_28_start - 0.5):
                        # -0.5 is for the fact that julday is zero at noon always, not midnight!
                        offset = 24
                    else:
                        offset = 0
                    t2 = temporal.Time(swe.revjul(gc_28_end)[3] + offset).toString()
                    # sys.stderr.write('gajacchhaya %d\n' % gc_28_d)

                    self.fest_days['gajacchAyA-yOgaH' +
                                   '-\\textsf{' + t1 + '}{\\RIGHTarrow}\\textsf{' +
                                   t2 + '}'] = [gc_28_d]
                    gc_28 = False
                if gc_30:
                    gc_30_start += tz_off / 24.0
                    gc_30_end += tz_off / 24.0
                    # sys.stderr.write('30: (%f, %f)\n' % (gc_30_start, gc_30_end))
                    gc_30_d = 1 + floor(gc_30_start - self.jd_start_utc)
                    t1 = temporal.Time(swe.revjul(gc_30_start)[3]).toString()

                    if floor(gc_30_end - 0.5) != floor(gc_30_start - 0.5):
                        offset = 24
                    else:
                        offset = 0
                    t2 = temporal.Time(swe.revjul(gc_30_end)[3] + offset).toString()
                    # sys.stderr.write('gajacchhaya %d\n' % gc_30_d)

                    self.fest_days['gajacchAyA-yOgaH' +
                                   '-\\textsf{' + t1 + '}{\\RIGHTarrow}\\textsf{' +
                                   t2 + '}'] = [gc_30_d]
                    gc_30 = False

            # AYUSHMAN BAVA SAUMYA
            if self.weekday[d] == 3 and temporal.get_angam(self.jd_sunrise[d],
                                                           temporal.YOGAM,
                                                           ayanamsha_id=self.ayanamsha_id) == 3:
                if temporal.get_angam(self.jd_sunrise[d], temporal.KARANAM,
                                      ayanamsha_id=self.ayanamsha_id) in list(range(2, 52, 7)):
                    self.add_festival('AyuSmAn-bava-saumya', d, debug_festivals)

            # VYATIPATAM
            if temporal.get_yoga(self.jd_sunrise[d], ayanamsha_id=self.ayanamsha_id) == 17 and \
                    self.solar_month[d] in [6, 9]:
                yogams_yest = self.get_angams_for_kaalas(d - 1, temporal.get_yoga, 'madhyaahna')
                if self.solar_month[d] == 9:
                    festival_name = 'mahAdhanurvyatIpAtam'
                elif self.solar_month[d] == 6:
                    festival_name = 'mahAvyatIpAtam'
                else:
                    # Can be used later, for marking Shannavati Tarpana days
                    festival_name = 'vyatIpAtam'
                if yogams_yest[0] == 17 or yogams_yest[1] == 17:
                    self.add_festival(festival_name, d - 1, debug_festivals)
                else:
                    self.add_festival(festival_name, d, debug_festivals)

            # 8 MAHA DWADASHIS
            if (self.tithi_sunrise[d] % 15) == 11 and (self.tithi_sunrise[d + 1] % 15) == 11:
                self.add_festival('unmIlanI~mahAdvAdazI', d + 1, debug_festivals)

            if (self.tithi_sunrise[d] % 15) == 12 and (self.tithi_sunrise[d + 1] % 15) == 12:
                self.add_festival('vyaJjulI~mahAdvAdazI', d, debug_festivals)

            if (self.tithi_sunrise[d] % 15) == 11 and (self.tithi_sunrise[d + 1] % 15) == 13:
                self.add_festival('trispRzA~mahAdvAdazI', d, debug_festivals)

            if (self.tithi_sunrise[d] % 15) == 0 and (self.tithi_sunrise[d + 1] % 15) == 0:
                # Might miss out on those parva days right after Dec 31!
                if (d - 3) > 0:
                    self.add_festival('pakSavardhinI~mahAdvAdazI', d - 3, debug_festivals)

            if self.nakshatram_sunrise[d] == 4 and (self.tithi_sunrise[d] % 15) == 12:
                self.add_festival('pApanAzinI~mahAdvAdazI', d, debug_festivals)

            if self.nakshatram_sunrise[d] == 7 and (self.tithi_sunrise[d] % 15) == 12:
                self.add_festival('jayantI~mahAdvAdazI', d, debug_festivals)

            if self.nakshatram_sunrise[d] == 8 and (self.tithi_sunrise[d] % 15) == 12:
                self.add_festival('jayA~mahAdvAdazI', d, debug_festivals)

            if self.nakshatram_sunrise[d] == 8 and (self.tithi_sunrise[d] % 15) == 12 and self.lunar_month[d] == 12:
                # Better checking needed (for other than sunrise).
                # Last occurred on 27-02-1961 - pushya nakshatra and phalguna krishna dvadashi (or shukla!?)
                self.add_festival('gOvinda~mahAdvAdazI', d, debug_festivals)

            if (self.tithi_sunrise[d] % 15) == 12:
                if self.nakshatram_sunrise[d] in [21, 22, 23]:
                    # We have a dwadashi near shravana, check for Shravana sparsha
                    for td in self.tithi_data[d:d + 2]:
                        (t12, t12_end) = td[0]
                        if t12_end is None:
                            continue
                        if (t12 % 15) == 11:
                            if temporal.get_angam(t12_end, temporal.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id) == 22:
                                if (self.tithi_sunrise[d] % 15) == 12 and (self.tithi_sunrise[d + 1] % 15) == 12:
                                    self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                                elif (self.tithi_sunrise[d] % 15) == 12:
                                    self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                                elif (self.tithi_sunrise[d + 1] % 15) == 12:
                                    self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1, debug_festivals)
                        if (t12 % 15) == 12:
                            if temporal.get_angam(t12_end, temporal.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id) == 22:
                                if (self.tithi_sunrise[d] % 15) == 12 and (self.tithi_sunrise[d + 1] % 15) == 12:
                                    self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                                elif (self.tithi_sunrise[d] % 15) == 12:
                                    self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                                elif (self.tithi_sunrise[d + 1] % 15) == 12:
                                    self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1, debug_festivals)

            if self.nakshatram_sunrise[d] == 22 and (self.tithi_sunrise[d] % 15) == 12:
                self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)

            # SPECIAL SAPTAMIs
            if self.weekday[d] == 0 and (self.tithi_sunrise[d] % 15) == 7:
                festival_name = 'bhAnusaptamI'
                if self.tithi_sunrise[d] == 7:
                    festival_name = 'vijayA' + '~' + festival_name
                if self.nakshatram_sunrise[d] == 27:
                    # Even more auspicious!
                    festival_name += '★'
                self.add_festival(festival_name, d, debug_festivals)

            if temporal.get_angam(self.jd_sunrise[d], temporal.NAKSHATRA_PADA,
                                  ayanamsha_id=self.ayanamsha_id) == 49 and \
                    self.tithi_sunrise[d] == 7:
                self.add_festival('bhadrA~saptamI', d, debug_festivals)

            if self.solar_month_end_time[d] is not None:
                # we have a Sankranti!
                if self.tithi_sunrise[d] == 7:
                    self.add_festival('mahAjayA~saptamI', d, debug_festivals)

            # VARUNI TRAYODASHI
            if self.lunar_month[d] == 12 and self.tithi_sunrise[d] == 28:
                if temporal.get_angam(self.jd_sunrise[d], temporal.NAKSHATRAM,
                                      ayanamsha_id=self.ayanamsha_id) == 24:
                    vtr_name = 'vAruNI~trayOdazI'
                    if self.weekday[d] == 6:
                        vtr_name = 'mahA' + vtr_name
                        if temporal.get_angam(self.jd_sunrise[d],
                                              temporal.YOGAM,
                                              ayanamsha_id=self.ayanamsha_id) == 23:
                            pref = 'mahA' + vtr_name
                    self.add_festival(vtr_name, d, debug_festivals)

            # SOMAMAVASYA
            if self.tithi_sunrise[d] == 30 and self.weekday[d] == 1:
                self.add_festival('sOmavatI amAvasyA', d, debug_festivals)
            if 30 in (self.get_angams_for_kaalas(d, temporal.get_tithi, 'aparaahna')[:2] + [self.tithi_sunrise[d]]) and self.weekday[d] in [1, 2, 4]:
                # Checking for sunrise and aparaahna. Not sure.
                self.add_festival('puSkalA amAvasyA (alabhyam)', d, debug_festivals)

            # MAHODAYAM
            # Can also refer youtube video https://youtu.be/0DBIwb7iaLE?list=PL_H2LUtMCKPjh63PRk5FA3zdoEhtBjhzj&t=6747
            # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Bhanuvasara = Ardhodayam
            # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Somavasara = Mahodayam
            if self.lunar_month[d] in [10, 11] and self.tithi_sunrise[d] == 30 or temporal.get_tithi(self.jd_sunset[d], ayanamsha_id=self.ayanamsha_id) == 30:
                if (temporal.get_angam(self.jd_sunrise[d], temporal.YOGAM, ayanamsha_id=self.ayanamsha_id) == 17 or temporal.get_angam(self.jd_sunset[d], temporal.YOGAM, ayanamsha_id=self.ayanamsha_id) == 17) and \
                        (temporal.get_angam(self.jd_sunrise[d], temporal.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id) == 22 or temporal.get_angam(self.jd_sunset[d], temporal.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id) == 22):
                    if self.weekday[d] == 1:
                        festival_name = 'mahOdaya-puNyakAlaH'
                        self.add_festival(festival_name, d, debug_festivals)
                        # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))
                    elif self.weekday[d] == 0:
                        festival_name = 'ardhOdaya-puNyakAlaH'
                        self.add_festival(festival_name, d, debug_festivals)
                        # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))

            # AMA-VYATIPATA YOGAH
            # श्रवणाश्विधनिष्ठार्द्रानागदैवतमापतेत् ।
            # रविवारयुतामायां व्यतीपातः स उच्यते ॥
            # व्यतीपाताख्ययोगोऽयं शतार्कग्रहसन्निभः ॥
            # “In Mahabharata, if on a Sunday, Amavasya and one of the stars –
            # Sravanam, Asvini, Avittam, Tiruvadirai or Ayilyam, occurs, then it is called ‘Vyatipatam’.
            # This Vyatipata yogam is equal to a hundred Surya grahanas in merit.”
            tithi_sunset = temporal.get_angam(self.jd_sunset[d], temporal.TITHI, ayanamsha_id=self.ayanamsha_id)
            if self.weekday[d] == 0 and (self.tithi_sunrise[d] == 30 or tithi_sunset == 30):
                # AMAVASYA on a Sunday
                if (self.nakshatram_sunrise[d] in [1, 6, 9, 22, 23] and self.tithi_sunrise[d] == 30) or\
                   (tithi_sunset == 30 and temporal.get_angam(self.jd_sunset[d], temporal.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id) in [1, 6, 9, 22, 23]):
                    festival_name = 'vyatIpAta-yOgaH (alabhyam)'
                    self.add_festival(festival_name, d, debug_festivals)
                    logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))

            # MANGALA-CHATURTHI
            if self.weekday[d] == 2 and (self.tithi_sunrise[d] % 15) == 4:
                festival_name = 'aGgAraka-caturthI'
                if self.tithi_sunrise[d] == 4:
                    festival_name = 'sukhA' + '~' + festival_name
                self.add_festival(festival_name, d, debug_festivals)

            # KRISHNA ANGARAKA CHATURDASHI
            if self.weekday[d] == 2 and self.tithi_sunrise[d] == 29:
                self.add_festival('kRSNAGgAraka-caturdazI-puNyakAlaH/yamatarpaNam', d, debug_festivals)

            # BUDHASHTAMI
            if self.weekday[d] == 3 and (self.tithi_sunrise[d] % 15) == 8:
                self.add_festival('budhASTamI', d, debug_festivals)

            # BHRGUVARA SUBRAHMANYA VRATAM
            if self.solar_month[d] == 7 and self.weekday[d] == 5:
                festival_name = 'bhRguvAra-subrahmaNya-vratam'
                if festival_name not in self.fest_days:
                    # only the first bhRguvAra of tulA mAsa is considered (skAnda purANam)
                    # https://youtu.be/rgXwyo0L3i8?t=222
                    self.add_festival(festival_name, d, debug_festivals)

            # AVANI NYAYITRUKIZHAMAI
            if self.solar_month[d] == 5 and self.weekday[d] == 0:
                self.add_festival('ta:AvaNi~JAyir2r2ukkizhamai', d, debug_festivals)

            # PURATTASI SANIKKIZHAMAI
            if self.solar_month[d] == 6 and self.weekday[d] == 6:
                self.add_festival('ta:puraTTAci~can2ikkizhamai', d, debug_festivals)

            # KARTHIKAI NYAYITRUKIZHAMAI
            if self.solar_month[d] == 8 and self.weekday[d] == 0:
                self.add_festival('ta:kArttigai~JAyir2r2ukkizhamai', d, debug_festivals)

            # KRTTIKA SOMAVASARA
            if self.lunar_month[d] == 8 and self.weekday[d] == 1:
                self.add_festival('kRttikA~sOmavAsaraH', d, debug_festivals)

            # AADI VELLI
            if self.solar_month[d] == 4 and self.weekday[d] == 5:
                self.add_festival('ta:ADi~veLLikkizhamai', d, debug_festivals)

            # TAI
            if self.solar_month[d] == 10 and self.weekday[d] == 5:
                self.add_festival('ta:tai~veLLikkizhamai', d, debug_festivals)

            # MASI SEVVAI
            if self.solar_month[d] == 11 and self.weekday[d] == 2:
                self.add_festival('ta:mAci~cevvAy', d, debug_festivals)

            # BHAUMASHWINI
            if (self.nakshatram_sunrise[d] == 27 or self.nakshatram_sunrise[d] == 1) and self.weekday[d] == 2:
                # Is it necessarily only at sunrise?
                angams = self.get_angams_for_kaalas(d, temporal.get_nakshatram, 'madhyaahna')
                if any(x == 1 for x in [self.nakshatram_sunrise[d], angams[0], angams[1]]):
                    # if any(x == 1 for x in [self.nakshatram_sunrise[d]]):
                    self.add_festival('bhaumAzvinI-puNyakAlaH', d, debug_festivals)

            # BUDHANURADHA
            if (self.nakshatram_sunrise[d] == 16 or self.nakshatram_sunrise[d] == 17) and self.weekday[d] == 3:
                # Is it necessarily only at sunrise?
                angams = self.get_angams_for_kaalas(d, temporal.get_nakshatram, 'madhyaahna')
                if any(x == 17 for x in [self.nakshatram_sunrise[d], angams[0], angams[1]]):
                    # if any(x == 17 for x in [self.nakshatram_sunrise[d]]):
                    self.add_festival('budhAnUrAdhA-puNyakAlaH', d, debug_festivals)

            # festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules_test.json'))
            festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
            assert "tripurOtsavaH" in festival_rules

            for festival_name in festival_rules:
                if 'month_type' in festival_rules[festival_name]:
                    month_type = festival_rules[festival_name]['month_type']
                else:
                    # Maybe only description of the festival is given, as computation has been
                    # done in computeFestivals(), without using a rule in festival_rules.json!
                    if 'description_short' in festival_rules[festival_name]:
                        continue
                    raise (ValueError, "No month_type mentioned for %s" % festival_name)
                if 'month_number' in festival_rules[festival_name]:
                    month_num = festival_rules[festival_name]['month_number']
                else:
                    raise (ValueError, "No month_num mentioned for %s" % festival_name)
                if 'angam_type' in festival_rules[festival_name]:
                    angam_type = festival_rules[festival_name]['angam_type']
                else:
                    raise (ValueError, "No angam_type mentioned for %s" % festival_name)
                if 'angam_number' in festival_rules[festival_name]:
                    angam_num = festival_rules[festival_name]['angam_number']
                else:
                    raise (ValueError, "No angam_num mentioned for %s" % festival_name)
                if 'kaala' in festival_rules[festival_name]:
                    kaala = festival_rules[festival_name]['kaala']
                else:
                    kaala = 'sunrise'  # default!
                if 'priority' in festival_rules[festival_name]:
                    priority = festival_rules[festival_name]['priority']
                else:
                    priority = 'puurvaviddha'
                # if 'titles' in festival_rules[festival_name]:
                #     fest_other_names = festival_rules[festival_name]['titles']
                # if 'Nirnaya' in festival_rules[festival_name]:
                #     fest_nirnaya = festival_rules[festival_name]['Nirnaya']
                # if 'references_primary' in festival_rules[festival_name]:
                #     fest_ref1 = festival_rules[festival_name]['references_primary']
                # if 'references_secondary' in festival_rules[festival_name]:
                #     fest_ref2 = festival_rules[festival_name]['references_secondary']
                # if 'comments' in festival_rules[festival_name]:
                #     fest_comments = festival_rules[festival_name]['comments']

                if angam_type == 'tithi' and month_type == 'lunar_month' and angam_num == 1:
                    # Shukla prathama tithis need to be dealt carefully, if e.g. the prathama tithi
                    # does not touch sunrise on either day (the regular check won't work, because
                    # the month itself is different the previous day!)
                    if self.tithi_sunrise[d] == 30 and self.tithi_sunrise[d + 1] == 2 and \
                            self.lunar_month[d + 1] == month_num:
                        # Only in this case, we have a problem
                        self.add_festival(festival_name, d, debug_festivals)
                        continue

                if angam_type == 'day' and month_type == 'solar_month' and self.solar_month[d] == month_num:
                    if self.solar_month_day[d] == angam_num:
                        self.fest_days[festival_name] = [d]
                elif (month_type == 'lunar_month' and ((self.lunar_month[d] == month_num or month_num == 0) or ((self.lunar_month[d + 1] == month_num and angam_num == 1)))) or \
                        (month_type == 'solar_month' and (self.solar_month[d] == month_num or month_num == 0)):
                    # Using 0 as a special tag to denote every month!
                    if angam_type == 'tithi':
                        angam_sunrise = self.tithi_sunrise
                        get_angam_func = temporal.get_tithi
                        num_angams = 30
                    elif angam_type == 'nakshatram':
                        angam_sunrise = self.nakshatram_sunrise
                        get_angam_func = temporal.get_nakshatram
                        num_angams = 27
                    elif angam_type == 'yogam':
                        angam_sunrise = self.yogam_sunrise
                        get_angam_func = temporal.get_yoga
                        num_angams = 27
                    else:
                        raise ValueError('Error; unknown string in rule: "%s"' % (angam_type))

                    if angam_num == 1:
                        prev_angam = num_angams
                    else:
                        prev_angam = angam_num - 1
                    next_angam = (angam_num % num_angams) + 1

                    fday = None

                    if angam_sunrise[d] == prev_angam or angam_sunrise[d] == angam_num:
                        angams = self.get_angams_for_kaalas(d, get_angam_func, kaala)
                        if angams is None:
                            sys.stderr.write('No angams returned! Skipping festival %s'
                                             % festival_name)
                            continue
                            # Some error, e.g. weird kaala, so skip festival
                        if debug_festivals:
                            print('%' * 80)
                            try:
                                print('%', festival_name, ': ', festival_rules[festival_name])
                                print("%%angams today & tmrw:", angams)
                            except KeyError:
                                print('%', festival_name, ': ', festival_rules[festival_name.split('\\')[0][:-1]])
                                print("%%angams today & tmrw:", angams)

                        if priority == 'paraviddha':
                            if angams[0] == angam_num and angams[1] == angam_num:
                                fday = d
                            if angams[2] == angam_num and angams[3] == angam_num:
                                fday = d + 1

                            if fday is None:
                                if festival_name not in self.fest_days:
                                    # logging.debug('%d: %s (%s)' % (d, angams, festival_name))
                                    if angams[1] == angam_num:
                                        # Angam not present at beginning of kala on Day 1, but present at end
                                        # Does not touch Day 2.
                                        fday = d
                                        if debug_festivals:
                                            logging.warning('%s did not touch start of %s kaala on d=%d or %d, but incident at end of kaala at d=%d. Assigning %d.' %
                                                            (jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES']['hk'][angam_num], kaala, d, d + 1, d, d))
                                    elif angams[1] == next_angam:
                                        fday = d  # Should be d - 1?
                                        logging.warning('Assigned paraviddha day for %s as %d with difficulty!' %
                                                        (festival_name, fday) + ' Please check for unusual cases.')

                            if fday is None:
                                if debug_festivals:
                                    print('%', angams, angam_num)
                                    if festival_name not in self.fest_days:
                                        logging.warning('Could not assign paraviddha day for %s!' %
                                                        festival_name +
                                                        ' Please check for unusual cases.\n')
                            # else:
                            #     sys.stderr.write('Assigned paraviddha day for %s!' %
                            #                      festival_name + ' Ignore future warnings!\n')
                        elif priority == 'puurvaviddha':
                            # angams_yest = self.get_angams_for_kaalas(d - 1, get_angam_func, kaala)
                            # if debug_festivals:
                            #     print("%angams yest & today:", angams_yest)
                            if angams[0] == angam_num or angams[1] == angam_num:
                                if festival_name in self.fest_days:
                                    # Check if yesterday was assigned already
                                    # to this puurvaviddha festival!
                                    if self.fest_days[festival_name].count(d - 1) == 0:
                                        fday = d
                                else:
                                    fday = d
                            elif angams[2] == angam_num or angams[3] == angam_num:
                                fday = d + 1
                            else:
                                # This means that the correct angam did not
                                # touch the kaala on either day!
                                if angams == [prev_angam, prev_angam, next_angam, next_angam]:
                                    # d_offset = {'sunrise': 0, 'aparaahna': 1, 'moonrise': 1, 'madhyaahna': 1, 'sunset': 1}[kaala]
                                    d_offset = 0 if kaala in ['sunrise', 'moonrise'] else 1
                                    if debug_festivals:
                                        logging.warning(
                                            '%d-%02d-%02d> %s: %s %d did not touch %s on either day: %s. Assigning today + %d' %
                                            (y, m, dt, festival_name, angam_type, angam_num, kaala, str(angams), d_offset))
                                    # Need to assign a day to the festival here
                                    # since the angam did not touch kaala on either day
                                    # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
                                    # THIS BEING PURVAVIDDHA
                                    # Perhaps just need better checking of
                                    # conditions instead of this fix
                                    if festival_name in self.fest_days:
                                        if self.fest_days[festival_name].count(d - 1 + d_offset) == 0:
                                            fday = d + d_offset
                                    else:
                                        fday = d + d_offset
                                else:
                                    if festival_name not in self.fest_days and angams != [prev_angam] * 4:
                                        logging.debug('Special case: %s; angams = %s' % (festival_name, str(angams)))

                        else:
                            logging.error('Unknown priority "%s" for %s! Check the rules!' % (priority, festival_name))

                    if fday is not None:
                        if (month_type == 'lunar_month' and ((self.lunar_month[d] == month_num or month_num == 0) or ((self.lunar_month[d + 1] == month_num and angam_num == 1)))) or \
                           (month_type == 'solar_month' and (self.solar_month[fday] == month_num or month_num == 0)):
                            # If month on fday is incorrect, we ignore and move.
                            if month_type == 'lunar_month' and angam_num == 1 and self.lunar_month[fday + 1] != month_num:
                                continue
                            if festival_name.find('\\') == -1 and \
                                    'kaala' in festival_rules[festival_name] and \
                                    festival_rules[festival_name]['kaala'] == 'arunodaya':
                                fday += 1
                            self.add_festival(festival_name, fday, debug_festivals)
                        else:
                            if debug_festivals:
                                if month_type == 'solar_month':
                                    logging.warning('Not adding festival %s on %d fday (month = %d instead of %d)' % (festival_name, fday, self.solar_month[fday], month_num))
                                else:
                                    logging.warning('Not adding festival %s on %d fday (month = %d instead of %d)' % (festival_name, fday, self.lunar_month[fday], month_num))

            # distance from prabhava
            samvatsara_id = (self.year - 1568) % 60 + 1
            new_yr = 'mESa-saGkrAntiH' + '~(' + temporal.NAMES['SAMVATSARA_NAMES']['hk'][(samvatsara_id % 60) + 1] + \
                     '-' + 'saMvatsaraH' + ')'

            if self.solar_month[d] == 1 and self.solar_month[d - 1] == 12:
                self.fest_days[new_yr] = [d]
                self.add_festival('paJcAGga-paThanam', d, debug_festivals)

        # Update festival numbers if they exist
        for festival_name in festival_rules:
            if festival_name in self.fest_days and 'year_start' in festival_rules[festival_name]:
                fest_start_year = festival_rules[festival_name]['year_start']
                month_type = festival_rules[festival_name]['month_type']
                if len(self.fest_days[festival_name]) > 1:
                    if self.fest_days[festival_name][1] - self.fest_days[festival_name][0] < 300:
                        # Lunar festivals can repeat after 354 days; Solar festivals "can" repeat after 330 days
                        # (last day of Dhanur masa Jan and first day of Dhanur masa Dec may have same nakshatra and are about 335 days apart)
                        # In fact they will be roughly 354 days apart, again!
                        logging.warning('Multiple occurrences of festival %s within year. Check?: %s' % (festival_name, str(self.fest_days[festival_name])))
                for assigned_day in self.fest_days[festival_name]:
                    if month_type == 'solar_month':
                        fest_num = self.year + 3100 + (assigned_day >= self.solar_month.index(1)) - fest_start_year + 1
                    elif month_type == 'lunar_month':
                        if festival_rules[festival_name]['angam_number'] == 1 and festival_rules[festival_name]['month_number'] == 1:
                            # Assigned day may be less by one, since prathama may have started after sunrise
                            # Still assume assigned_day >= self.lunar_month.index(1)!
                            fest_num = self.year + 3100 + (1) - fest_start_year + 1
                        else:
                            fest_num = self.year + 3100 + (assigned_day >= self.lunar_month.index(1)) - fest_start_year + 1

                    if fest_num <= 0:
                        logging.warning('Festival %s is only in the future!' % festival_name)
                    else:
                        if festival_name not in self.fest_days:
                            logging.warning('Did not find festival %s to be assigned. Dhanurmasa festival?' % festival_name)
                            continue
                        festival_name_updated = festival_name + '~\\#{%d}' % fest_num
                        # logging.debug('Changing %s to %s' % (festival_name, festival_name_updated))
                        if festival_name_updated in self.fest_days:
                            logging.warning('Overwriting festival day for %s %d with %d.' % (festival_name_updated, self.fest_days[festival_name_updated][0], assigned_day))
                            self.fest_days[festival_name_updated] = [assigned_day]
                        else:
                            self.fest_days[festival_name_updated] = [assigned_day]
                del(self.fest_days[festival_name])

        # If tripurotsava coincides with maha kArtikI (kRttikA nakShatram)
        # only then it is mahAkArtikI
        # else it is only tripurotsava
        if 'tripurOtsavaH' not in self.fest_days:
            logging.error('tripurOtsavaH not in self.fest_days!')
        else:
            if self.fest_days['tripurOtsavaH'] != self.fest_days['mahA~kArtikI']:
                del self.fest_days['mahA~kArtikI']
                # An error here implies the festivals were not assigned: adhika
                # mAsa calc errors??

    def assign_relative_festivals(self):
        # Add "RELATIVE" festivals --- festivals that happen before or
        # after other festivals with an exact timedelta!
        if 'yajurvEda-upAkarma' not in self.fest_days:
            logging.error('yajurvEda-upAkarma not in festivals!')
        else:
            self.fest_days['varalakSmI-vratam'] = [self.fest_days['yajurvEda-upAkarma'][0] -
                                                   ((self.weekday_start - 1 + self.fest_days['yajurvEda-upAkarma'][
                                                       0] - 5) % 7)]

        relative_festival_rules = read_old_festival_rules_dict(
            os.path.join(CODE_ROOT, 'panchangam/data/relative_festival_rules.json'))

        for festival_name in relative_festival_rules:
            offset = int(relative_festival_rules[festival_name]['offset'])
            rel_festival_name = relative_festival_rules[festival_name]['anchor_festival_id']
            if rel_festival_name not in self.fest_days:
                # Check approx. match
                matched_festivals = []
                for fest_key in self.fest_days:
                    if fest_key.startswith(rel_festival_name):
                        matched_festivals += [fest_key]
                if matched_festivals == []:
                    logging.error('Relative festival %s not in fest_days!' % rel_festival_name)
                elif len(matched_festivals) > 1:
                    logging.error('Relative festival %s not in fest_days! Found more than one approximate match: %s' % (rel_festival_name, str(matched_festivals)))
                else:
                    self.fest_days[festival_name] = [self.fest_days[matched_festivals[0]][-1] + offset]
            else:
                self.fest_days[festival_name] = [self.fest_days[rel_festival_name][-1] + offset]

        # self.fest_days['ta:kapAlI veLLi bhUta vAhan2am'] = [panguni_uttaram - 6]
        # self.fest_days['ta:kapAlI bhikSATan2ar'] = [panguni_uttaram - 1]

        # if debugFestivals:
        #     print('%', self.fest_days)

        for festival_name in self.fest_days:
            for j in range(0, len(self.fest_days[festival_name])):
                self.festivals[self.fest_days[festival_name][j]].append(festival_name)

        # def check_festivals(self):
        festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
        for festival_name in festival_rules:
            result = [(key, value) for key, value in self.fest_days.items() if key.startswith(festival_name)]
            if len(result) == 0:
                logging.warning('Unable to assign day for %s' % festival_name)

    def compute_solar_eclipses(self):
        # Set location
        swe.set_topo(lon=self.city.longitude, lat=self.city.latitude, alt=0.0)
        jd = self.jd_start_utc
        while 1:
            next_eclipse_sol = swe.sol_eclipse_when_loc(julday=jd, lon=self.city.longitude, lat=self.city.latitude)
            [y, m, dt, t] = swe.revjul(next_eclipse_sol[1][0])
            local_time = tz(self.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
            # checking @ 6am local - can we do any better?
            tz_off = (datetime.utcoffset(local_time).days * 86400 +
                      datetime.utcoffset(local_time).seconds) / 3600.0
            # compute offset from UTC
            jd = next_eclipse_sol[1][0] + (tz_off / 24.0)
            jd_eclipse_solar_start = next_eclipse_sol[1][1] + (tz_off / 24.0)
            jd_eclipse_solar_end = next_eclipse_sol[1][4] + (tz_off / 24.0)
            # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
            eclipse_y = swe.revjul(jd - 1)[0]
            if eclipse_y != self.year:
                break
            else:
                fday = int(floor(jd) - floor(self.jd_start_utc) + 1)
                if (jd < (self.jd_sunrise[fday] + tz_off / 24.0)):
                    fday -= 1
                eclipse_solar_start = swe.revjul(jd_eclipse_solar_start)[3]
                eclipse_solar_end = swe.revjul(jd_eclipse_solar_end)[3]
                if (jd_eclipse_solar_start - (tz_off / 24.0)) == 0.0 or \
                        (jd_eclipse_solar_end - (tz_off / 24.0)) == 0.0:
                    # Move towards the next eclipse... at least the next new
                    # moon (>=25 days away)
                    jd += temporal.MIN_DAYS_NEXT_ECLIPSE
                    continue
                if eclipse_solar_end < eclipse_solar_start:
                    eclipse_solar_end += 24
                sunrise_eclipse_day = swe.revjul(self.jd_sunrise[fday] + (tz_off / 24.0))[3]
                sunset_eclipse_day = swe.revjul(self.jd_sunset[fday] + (tz_off / 24.0))[3]
                if eclipse_solar_start < sunrise_eclipse_day:
                    eclipse_solar_start = sunrise_eclipse_day
                if eclipse_solar_end > sunset_eclipse_day:
                    eclipse_solar_end = sunset_eclipse_day
                solar_eclipse_str = 'sUrya-grahaNam' + \
                                    '~\\textsf{' + temporal.Time(eclipse_solar_start).toString() + \
                                    '}{\\RIGHTarrow}\\textsf{' + temporal.Time(
                    eclipse_solar_end).toString() + '}'
                if self.weekday[fday] == 0:
                    solar_eclipse_str = '★cUDAmaNi-' + solar_eclipse_str
                self.festivals[fday].append(solar_eclipse_str)
            jd = jd + temporal.MIN_DAYS_NEXT_ECLIPSE

    def compute_lunar_eclipses(self):
        # Set location
        swe.set_topo(lon=self.city.longitude, lat=self.city.latitude, alt=0.0)
        jd = self.jd_start_utc
        while 1:
            next_eclipse_lun = swe.lun_eclipse_when(jd)
            [y, m, dt, t] = swe.revjul(next_eclipse_lun[1][0])
            local_time = tz(self.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
            # checking @ 6am local - can we do any better? This is crucial,
            # since DST changes before 6 am
            tz_off = (datetime.utcoffset(local_time).days * 86400 +
                      datetime.utcoffset(local_time).seconds) / 3600.0
            # compute offset from UTC
            jd = next_eclipse_lun[1][0] + (tz_off / 24.0)
            jd_eclipse_lunar_start = next_eclipse_lun[1][2] + (tz_off / 24.0)
            jd_eclipse_lunar_end = next_eclipse_lun[1][3] + (tz_off / 24.0)
            # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
            eclipse_y = swe.revjul(jd - 1)[0]
            if eclipse_y != self.year:
                break
            else:
                eclipse_lunar_start = swe.revjul(jd_eclipse_lunar_start)[3]
                eclipse_lunar_end = swe.revjul(jd_eclipse_lunar_end)[3]
                if (jd_eclipse_lunar_start - (tz_off / 24.0)) == 0.0 or \
                        (jd_eclipse_lunar_end - (tz_off / 24.0)) == 0.0:
                    # Move towards the next eclipse... at least the next full
                    # moon (>=25 days away)
                    jd += temporal.MIN_DAYS_NEXT_ECLIPSE
                    continue
                fday = int(floor(jd_eclipse_lunar_start) - floor(self.jd_start_utc) + 1)
                # print '%%', jd, fday, self.jd_sunrise[fday],
                # self.jd_sunrise[fday-1]
                if (jd < (self.jd_sunrise[fday] + tz_off / 24.0)):
                    fday -= 1
                if eclipse_lunar_start < swe.revjul(self.jd_sunrise[fday + 1] + tz_off / 24.0)[3]:
                    eclipse_lunar_start += 24
                # print '%%', jd, fday, self.jd_sunrise[fday],
                # self.jd_sunrise[fday-1], eclipse_lunar_start,
                # eclipse_lunar_end
                jd_moonrise_eclipse_day = swe.rise_trans(
                    jd_start=self.jd_sunrise[fday], body=swe.MOON, lon=self.city.longitude,
                    lat=self.city.latitude, rsmi=CALC_RISE)[1][0] + (tz_off / 24.0)
                jd_moonset_eclipse_day = swe.rise_trans(
                    jd_start=jd_moonrise_eclipse_day, body=swe.MOON, lon=self.city.longitude,
                    lat=self.city.latitude, rsmi=CALC_SET)[1][0] + (tz_off / 24.0)

                if eclipse_lunar_end < eclipse_lunar_start:
                    eclipse_lunar_end += 24

                if jd_eclipse_lunar_end < jd_moonrise_eclipse_day or \
                        jd_eclipse_lunar_start > jd_moonset_eclipse_day:
                    # Move towards the next eclipse... at least the next full
                    # moon (>=25 days away)
                    jd += temporal.MIN_DAYS_NEXT_ECLIPSE
                    continue

                moonrise_eclipse_day = swe.revjul(jd_moonrise_eclipse_day)[3]
                moonset_eclipse_day = swe.revjul(jd_moonset_eclipse_day)[3]

                if jd_eclipse_lunar_start < jd_moonrise_eclipse_day:
                    eclipse_lunar_start = moonrise_eclipse_day
                if jd_eclipse_lunar_end > jd_moonset_eclipse_day:
                    eclipse_lunar_end = moonset_eclipse_day

                if swe.calc_ut(jd_eclipse_lunar_end, swe.MOON)[0] < swe.calc_ut(jd_eclipse_lunar_end, swe.SUN)[0]:
                    grasta = 'rAhugrasta'
                else:
                    grasta = 'kEtugrasta'

                lunar_eclipse_str = 'candra-grahaNam~(' + grasta + ')' + \
                                    '~\\textsf{' + temporal.Time(eclipse_lunar_start).toString() + \
                                    '}{\\RIGHTarrow}\\textsf{' + temporal.Time(eclipse_lunar_end).toString() + '}'
                if self.weekday[fday] == 1:
                    lunar_eclipse_str = '★cUDAmaNi-' + lunar_eclipse_str

                self.festivals[fday].append(lunar_eclipse_str)
            jd += temporal.MIN_DAYS_NEXT_ECLIPSE

    def computeTransits(self):
        jd_end = self.jd_start_utc + temporal.MAX_DAYS_PER_YEAR
        check_window = 400  # Max t between two Jupiter transits is ~396 (checked across 180y)
        # Let's check for transitions in a relatively large window
        # to finalise what is the FINAL transition post retrograde movements
        transits = temporal.get_planet_next_transit(self.jd_start_utc, jd_end + check_window,
                                                    swe.JUPITER, ayanamsha_id=self.ayanamsha_id)
        if len(transits) > 0:
            for i, (jd_transit, rashi1, rashi2) in enumerate(transits):
                if self.jd_start_utc < jd_transit < jd_end:
                    fday = int(floor(jd_transit) - floor(self.jd_start_utc) + 1)
                    self.festivals[fday].append('guru-saGkrAntiH~(%s##\\To{}##%s)' %
                                                (temporal.NAMES['RASHI_NAMES']['hk'][rashi1],
                                                 temporal.NAMES['RASHI_NAMES']['hk'][rashi2]))
                    if rashi1 < rashi2 and transits[i + 1][1] < transits[i + 1][2]:
                        # Considering only non-retrograde transits for pushkara computations
                        # logging.debug('Non-retrograde transit; we have a pushkaram!')
                        (madhyanha_start, madhyaahna_end) = temporal.get_kaalas(self.jd_sunrise[fday],
                                                                                self.jd_sunset[fday], 2, 5)
                        if jd_transit < madhyaahna_end:
                            fday_pushkara = fday
                        else:
                            fday_pushkara = fday + 1
                        self.add_festival('%s-Adi-puSkara-ArambhaH' % temporal.NAMES['PUSHKARA_NAMES']['hk'][rashi2],
                                          fday_pushkara, debug=False)
                        self.add_festival('%s-Adi-puSkara-samApanam' % temporal.NAMES['PUSHKARA_NAMES']['hk'][rashi2],
                                          fday_pushkara + 11, debug=False)
                        self.add_festival('%s-antya-puSkara-samApanam' % temporal.NAMES['PUSHKARA_NAMES']['hk'][rashi1],
                                          fday_pushkara - 1, debug=False)
                        self.add_festival('%s-antya-puSkara-ArambhaH' % temporal.NAMES['PUSHKARA_NAMES']['hk'][rashi1],
                                          fday_pushkara - 12, debug=False)

        # transits = temporal.get_planet_next_transit(self.jd_start, jd_end,
        #                                    swe.SATURN, ayanamsha_id=self.ayanamsha_id)
        # if len(transits) > 0:
        #     for jd_transit, rashi1, rashi2 in transits:
        #         fday = int(floor(jd_transit) - floor(self.jd_start) + 1)
        #         self.festivals[fday].append('zani-saGkrAntiH~(%s##\\To{}##%s)' %
        #                                     (temporal.NAMES['RASHI']['hk'][rashi1],
        #                                     temporal.NAMES['RASHI']['hk'][rashi2]))

    def write_debug_log(self):
        log_file = open('cal-%4d-%s-log.txt' % (self.year, self.city.name), 'w')
        # helper_functions.MAX_SZ = 368
        for d in range(1, temporal.MAX_SZ - 1):
            jd = self.jd_start_utc - 1 + d
            [y, m, dt, t] = swe.revjul(jd)
            longitude_sun_sunset = swe.calc_ut(self.jd_sunset[d], swe.SUN)[0] - swe.get_ayanamsa(self.jd_sunset[d])
            log_data = '%02d-%02d-%4d\t[%3d]\tsun_rashi=%8.3f\ttithi=%8.3f\tsolar_month\
        =%2d\tlunar_month=%4.1f\n' % (dt, m, y, d, (longitude_sun_sunset % 360) / 30.0,
                                      temporal.get_angam_float(self.jd_sunrise[d],
                                                               temporal.TITHI,
                                                               ayanamsha_id=self.ayanamsha_id),
                                      self.solar_month[d], self.lunar_month[d])
            log_file.write(log_data)

    def update_festival_details(self):
        """

        Festival data may be updated more frequently and a precomputed panchangam may go out of sync. Hence we keep this method separate.
        :return:
        """
        self.reset_festivals()
        self.computeTransits()
        self.compute_solar_eclipses()
        self.compute_lunar_eclipses()
        self.compute_festivals()
        self.assign_relative_festivals()

    def add_details(self, compute_lagnams=False):
        self.compute_angams(compute_lagnams=compute_lagnams)
        self.assignLunarMonths()
        # self.update_festival_details()

    def reset_festivals(self, compute_lagnams=False):
        self.fest_days = {}
        # Pushkaram starting on 31 Jan might not get over till 12 days later
        self.festivals = [[] for _x in range(temporal.MAX_SZ + 15)]


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])


# logging.debug(common.json_class_index)


def get_panchangam(city, year, script, compute_lagnams=False, precomputed_json_dir="~/Documents"):
    fname_det = os.path.expanduser('%s/%s-%s-detailed.json' % (precomputed_json_dir, city.name, year))
    fname = os.path.expanduser('%s/%s-%s.json' % (precomputed_json_dir, city.name, year))

    if os.path.isfile(fname) and not compute_lagnams:
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
        return JsonObject.read_from_file(filename=fname)
    elif os.path.isfile(fname_det):
        # Load pickle, do not compute!
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
        return JsonObject.read_from_file(filename=fname_det)
    else:
        sys.stderr.write('No precomputed data available. Computing panchangam...\n')
        panchangam = Panchangam(city=city, year=year, script=script, compute_lagnams=compute_lagnams)
        sys.stderr.write('Writing computed panchangam to %s...\n' % fname)

        try:
            if compute_lagnams:
                panchangam.dump_to_file(filename=fname_det)
            else:
                panchangam.dump_to_file(filename=fname)
        except EnvironmentError:
            logging.warning("Not able to save.")
            logging.error(traceback.format_exc())
        # Save without festival details
        # Festival data may be updated more frequently and a precomputed panchangam may go out of sync. Hence we keep this method separate.
        panchangam.update_festival_details()
        return panchangam


if __name__ == '__main__':
    city = spatio_temporal.City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
    panchangam = Panchangam(city=city, year=2019, script=sanscript.DEVANAGARI, ayanamsha_id=swe.SIDM_LAHIRI, compute_lagnams=False)