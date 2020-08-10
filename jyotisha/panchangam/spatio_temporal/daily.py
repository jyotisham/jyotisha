#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import datetime
import logging
import swisseph as swe
import sys
from math import floor

from scipy.optimize import brentq

from jyotisha.panchangam import temporal
from jyotisha.panchangam.spatio_temporal import City, CALC_RISE, CALC_SET
from jyotisha.panchangam.temporal import SOLAR_MONTH, get_angam, get_angam_float, Time

from sanskrit_data.schema import common

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")


# This class is not named Panchangam in order to be able to disambiguate from annual.Panchangam in serialized objects.
class DailyPanchanga(common.JsonObject):
    """This class enables the construction of a panchangam
      """
    @classmethod
    def from_city_and_julian_day(cls, city, julian_day, ayanamsha_id=swe.SIDM_LAHIRI):
        (year, month, day, hours, minutes, seconds) = city.julian_day_to_local_time(julian_day)
        return DailyPanchanga(city=city, year=year, month=month, day=day, ayanamsha_id=ayanamsha_id)

    def __init__(self, city: City, year: int, month: int, day: int, ayanamsha_id: int = swe.SIDM_LAHIRI, previous_day_panchangam=None) -> None:
        """Constructor for the panchangam.
        """
        super(DailyPanchanga, self).__init__()
        self.city = city
        (self.year, self.month, self.day) = (year, month, day)
        self.julian_day_start = self.city.local_time_to_julian_day(year=self.year, month=self.month, day=self.day, hours=0, minutes=0, seconds=0)

        self.weekday = datetime.date(year=self.year, month=self.month, day=self.day).isoweekday() % 7
        self.ayanamsha_id = ayanamsha_id
        swe.set_sid_mode(ayanamsha_id)

        self.jd_sunrise = None
        self.jd_sunset = None
        self.jd_previous_sunset = None
        self.jd_next_sunrise = None
        self.jd_moonrise = None
        self.jd_moonset = None
        self.compute_sun_moon_transitions(previous_day_panchangam=previous_day_panchangam)

        self.tb_muhuurtas = None
        self.lagna_data = None
        self.kaalas = None

        self.solar_month_day = None
        self.solar_month_end_jd = None

        self.tithi_data = None
        self.tithi_at_sunrise = None
        self.nakshatram_data = None
        self.nakshatram_at_sunrise = None
        self.yoga_data = None
        self.yoga_at_sunrise = None
        self.karanam_data = None
        self.rashi_data = None

        self.festivals = []

    def compute_sun_moon_transitions(self, previous_day_panchangam=None, force_recomputation=False):
        """

        :param previous_day_panchangam: Panchangam for previous day, to avoid unnecessary calculations. (rise_trans calculations can be time consuming.)
        :param force_recomputation: Boolean indicating if the transitions should be recomputed. (rise_trans calculations can be time consuming.)
        :return:
        """
        if force_recomputation or self.jd_sunrise is None:
            if previous_day_panchangam is not None and previous_day_panchangam.jd_next_sunrise is not None:
                self.jd_sunrise = previous_day_panchangam.jd_next_sunrise
            else:
                self.jd_sunrise = swe.rise_trans(
                    jd_start=self.julian_day_start, body=swe.SUN,
                    lon=self.city.longitude, lat=self.city.latitude,
                    rsmi=CALC_RISE)[1][0]
        if force_recomputation or self.jd_sunset is None:
            self.jd_sunset = swe.rise_trans(
                jd_start=self.jd_sunrise, body=swe.SUN,
                lon=self.city.longitude, lat=self.city.latitude,
                rsmi=CALC_SET)[1][0]
        if force_recomputation or self.jd_previous_sunset is None:
            if previous_day_panchangam is not None and previous_day_panchangam.jd_sunset is not None:
                self.jd_previous_sunset = previous_day_panchangam.jd_sunset
            else:
                self.jd_previous_sunset = swe.rise_trans(
                    jd_start=self.jd_sunrise - 1, body=swe.SUN,
                    lon=self.city.longitude, lat=self.city.latitude,
                    rsmi=CALC_SET)[1][0]
        if force_recomputation or self.jd_next_sunrise is None:
            self.jd_next_sunrise = swe.rise_trans(
                jd_start=self.jd_sunset, body=swe.SUN,
                lon=self.city.longitude, lat=self.city.latitude,
                rsmi=CALC_RISE)[1][0]
        if self.jd_sunset == 0.0:
            logging.error('No sunset was computed!')
            raise (ValueError(
                'No sunset was computed. Perhaps the co-ordinates are beyond the polar circle (most likely a LAT-LONG swap! Please check your inputs.'))
            # logging.debug(swe.rise_trans(jd_start=jd_start, body=swe.SUN, lon=city.longitude,
            #                              lat=city.latitude, rsmi=CALC_SET))

        if force_recomputation or self.jd_moonrise is None:
            self.jd_moonrise = swe.rise_trans(
                jd_start=self.jd_sunrise,
                body=swe.MOON, lon=self.city.longitude,
                lat=self.city.latitude,
                rsmi=CALC_RISE)[1][0]
        if force_recomputation or self.jd_moonset is None:
            self.jd_moonset = swe.rise_trans(
                jd_start=self.jd_sunrise, body=swe.MOON,
                lon=self.city.longitude, lat=self.city.latitude,
                rsmi=CALC_SET)[1][0]

        self.tithi_data = temporal.get_angam_data(self.jd_sunrise, self.jd_next_sunrise, temporal.TITHI, ayanamsha_id=self.ayanamsha_id)
        self.tithi_at_sunrise = self.tithi_data[0][0]
        self.nakshatram_data = temporal.get_angam_data(self.jd_sunrise, self.jd_next_sunrise, temporal.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id)
        self.nakshatram_at_sunrise = self.nakshatram_data[0][0]
        self.yoga_data = temporal.get_angam_data(self.jd_sunrise, self.jd_next_sunrise, temporal.YOGA, ayanamsha_id=self.ayanamsha_id)
        self.yoga_at_sunrise = self.yoga_data[0][0]
        self.karanam_data = temporal.get_angam_data(self.jd_sunrise, self.jd_next_sunrise, temporal.KARANAM, ayanamsha_id=self.ayanamsha_id)
        self.rashi_data = temporal.get_angam_data(self.jd_sunrise, self.jd_next_sunrise, temporal.RASHI, ayanamsha_id=self.ayanamsha_id)

    def compute_solar_month(self):
        if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
            self.compute_sun_moon_transitions()
        swe.set_sid_mode(self.ayanamsha_id)
        self.longitude_sun_sunrise = swe.calc_ut(self.jd_sunrise, swe.SUN)[0] - swe.get_ayanamsa(self.jd_sunrise)
        self.longitude_sun_sunset = swe.calc_ut(self.jd_sunset, swe.SUN)[0] - swe.get_ayanamsa(self.jd_sunset)

        # Each solar month has 30 days. So, divide the longitude by 30 to get the solar month.
        self.solar_month_sunset = int(1 + floor((self.longitude_sun_sunset % 360) / 30.0))
        self.solar_month_sunrise = int(1 + floor(((self.longitude_sun_sunrise) % 360) / 30.0))
        # if self.solar_month_sunset != self.solar_month_sunrise:
        #   # sankrAnti.
        #   [_m, self.solar_month_end_jd] = temporal.get_angam_data(
        #     self.jd_sunrise, self.jd_next_sunrise, temporal.SOLAR_MONTH,
        #     ayanamsha_id=self.ayanamsha_id)[0]

    def compute_tb_muhuurtas(self):
        """ Computes muhuurta-s according to taittiriiya brAhmaNa.
        """
        if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
            self.compute_sun_moon_transitions()
        day_length_jd = self.jd_sunset - self.jd_sunrise
        muhuurta_length_jd = day_length_jd / (5 * 3)
        import numpy
        # 15 muhUrta-s in a day.
        muhuurta_starts = numpy.arange(self.jd_sunrise, self.jd_sunset, muhuurta_length_jd)[0:15]
        from jyotisha.panchangam import spatio_temporal
        self.tb_muhuurtas = [spatio_temporal.TbSayanaMuhuurta(
            city=self.city, jd_start=jd_start, jd_end=jd_start + muhuurta_length_jd,
            muhuurta_id=int((jd_start - self.jd_sunrise + muhuurta_length_jd / 10) / muhuurta_length_jd))
            for jd_start in muhuurta_starts]

    def compute_solar_day(self):
        """Compute the solar month and day for a given Julian day
        """
        # If solar transition happens before the current sunset but after the previous sunset, then that is taken to be solar day 1. Number of sunsets since the past solar month transition gives the solar day number.
        if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
            self.compute_sun_moon_transitions()
        self.solar_month = get_angam(self.jd_sunset, SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id)
        target = ((floor(get_angam_float(self.jd_sunset, SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id)) - 1) % 12) + 1

        # logging.debug(jd_start)
        # logging.debug(jd_sunset)
        # logging.debug(target)
        # logging.debug(get_angam_float(jd_sunset - 34, SOLAR_MONTH, -target, ayanamsha_id, False))
        # logging.debug(get_angam_float(jd_sunset + 1, SOLAR_MONTH, -target, ayanamsha_id, False))
        jd_masa_transit = brentq(get_angam_float, self.jd_sunrise - 34, self.jd_sunset,
                                 args=(SOLAR_MONTH, -target, self.ayanamsha_id, False))

        jd_sunset_after_masa_transit = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                                      lon=self.city.longitude, lat=self.city.latitude,
                                                      rsmi=CALC_SET)[1][0]

        jd_sunrise_after_masa_transit = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                                       lon=self.city.longitude, lat=self.city.latitude,
                                                       rsmi=CALC_RISE)[1][0]

        if jd_sunset_after_masa_transit > jd_sunrise_after_masa_transit:
            # Masa begins after sunset and before sunrise
            # Therefore Masa 1 is on the day when the sun rises next
            solar_month_day = floor(self.jd_sunset - jd_sunrise_after_masa_transit) + 1
        else:
            # Masa has started before sunset
            solar_month_day = round(self.jd_sunset - jd_sunset_after_masa_transit) + 1
        self.solar_month_day = solar_month_day

    def get_lagna_float(self, jd, offset=0, debug=False):
        """Returns the angam

          Args:
            :param jd: The Julian Day at which the lagnam is to be computed
            :param offset: Used by internal functions for bracketing
            :param debug

          Returns:
            float lagna
        """
        swe.set_sid_mode(self.ayanamsha_id)
        lcalc = swe.houses_ex(jd, self.city.latitude, self.city.longitude)[1][0] - swe.get_ayanamsa_ut(jd)
        lcalc = lcalc % 360

        if offset == 0:
            return lcalc / 30

        else:
            if debug:
                logging.debug(debug)
                logging.debug(('offset:', offset))
                logging.debug(('lcalc/30', lcalc / 30))
                logging.debug(('lcalc/30 + offset = ', lcalc / 30 + offset))

            # The max expected value is somewhere between 2 and -2, with bracketing

            if (lcalc / 30 + offset) >= 3:
                return (lcalc / 30) + offset - 12
            elif (lcalc / 30 + offset) <= -3:
                return (lcalc / 30)
            else:
                return (lcalc / 30) + offset

    def get_lagna_data(self, debug=False):
        """Returns the lagna data

            Args:
              debug

            Returns:
              tuples detailing the end time of each lagna, beginning with the one
              prevailing at sunrise
            """
        if self.lagna_data is not None:
            return self.lagna_data

        self.lagna_data = []
        if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
            self.compute_sun_moon_transitions()
        lagna_sunrise = 1 + floor(self.get_lagna_float(self.jd_sunrise))

        lagna_list = [(x + lagna_sunrise - 1) % 12 + 1 for x in range(13)]

        lbrack = self.jd_sunrise - 3 / 24
        rbrack = self.jd_sunrise + 3 / 24

        for lagna in lagna_list:
            # print('---\n', lagna)
            if (debug):
                logging.debug(('lagna sunrise', self.get_lagna_float(self.jd_sunrise)))
                logging.debug(('lbrack', self.get_lagna_float(lbrack, int(-lagna))))
                logging.debug(('rbrack', self.get_lagna_float(rbrack, int(-lagna))))

            lagna_end_time = brentq(self.get_lagna_float, lbrack, rbrack,
                                    args=(-lagna, debug))
            lbrack = lagna_end_time + 1 / 24
            rbrack = lagna_end_time + 3 / 24
            if lagna_end_time < self.jd_next_sunrise:
                self.lagna_data.append((lagna, lagna_end_time))
        return self.lagna_data

    def get_kaalas(self):
        # Compute the various kaalas
        # Sunrise/sunset and related stuff (like rahu, yama)
        if self.kaalas is not None:
            return self.kaalas

        if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
            self.compute_sun_moon_transitions()
        YAMAGANDA_OCTETS = [4, 3, 2, 1, 0, 6, 5]
        RAHUKALA_OCTETS = [7, 1, 6, 4, 5, 3, 2]
        GULIKAKALA_OCTETS = [6, 5, 4, 3, 2, 1, 0]
        self.kaalas = {
            'braahma': temporal.get_kaalas(self.jd_previous_sunset, self.jd_sunrise, 13, 15),
            'prAtaH sandhyA': temporal.get_kaalas(self.jd_previous_sunset, self.jd_sunrise, 14, 15),
            'prAtaH sandhyA end': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 4, 15),
            'prAtah': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 0, 5),
            'saGgava': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 1, 5),
            'madhyAhna': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 2, 5),
            'mAdhyAhnika sandhyA': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 5, 15),
            'mAdhyAhnika sandhyA end': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 13, 15),
            'aparAhna': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 3, 5),
            'sAyAhna': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 4, 5),
            'sAyaM sandhyA': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset, 14, 15),
            'sAyaM sandhyA end': temporal.get_kaalas(self.jd_sunset, self.jd_next_sunrise, 1, 15),
            'rAtri yAma 1': temporal.get_kaalas(self.jd_sunset, self.jd_next_sunrise, 1, 4),
            'zayana': temporal.get_kaalas(self.jd_sunset, self.jd_next_sunrise, 3, 8),
            'dinAnta': temporal.get_kaalas(self.jd_sunset, self.jd_next_sunrise, 5, 8),
            'rahu': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset,
                                        RAHUKALA_OCTETS[self.weekday], 8),
            'yama': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset,
                                        YAMAGANDA_OCTETS[self.weekday], 8),
            'gulika': temporal.get_kaalas(self.jd_sunrise, self.jd_sunset,
                                          GULIKAKALA_OCTETS[self.weekday], 8)
        }
        return self.kaalas

    def get_kaalas_local_time(self, format='hh:mm*'):
        kaalas = self.get_kaalas()
        return {x: (Time((kaalas[x][0] - self.julian_day_start) * 24).toString(format=format),
                    Time((kaalas[x][1] - self.julian_day_start) * 24).toString(format=format)) for x in kaalas}

    def update_festival_details(self):
        pass


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


if __name__ == '__main__':
    panchangam = DailyPanchanga.from_city_and_julian_day(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'), julian_day=2457023.27)
    panchangam.compute_tb_muhuurtas()
    logging.debug(str(panchangam))
