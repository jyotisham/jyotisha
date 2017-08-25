#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import swisseph as swe
from math import floor

from scipy.optimize import brentq

from jyotisha.panchangam.custom_transliteration import sexastr2deci
from jyotisha.panchangam.temporal import get_angam_float, get_angam, SOLAR_MONTH


# next new/full moon from current one is at least 27.3 days away


class City(object):

    """This class enables the construction of a city object
    """

    def __init__(self, name, latitude, longitude, timezone):
        """Constructor for city"""
        self.name = name
        self.latstr = latitude
        self.lonstr = longitude
        self.latitude = sexastr2deci(latitude)
        self.longitude = sexastr2deci(longitude)
        self.timezone = timezone


def get_lagna_float(jd, lat, lon, offset=0, ayanamsha_id=swe.SIDM_LAHIRI, debug=False):
    """Returns the angam

      Args:
        float jd: The Julian Day at which the lagnam is to be computed
        lat: Latitude of the place where the lagnam is to be computed
        lon: Longitude of the place where the lagnam is to be computed
        offset: Used by internal functions for bracketing

      Returns:
        float lagna

      Examples:
        >>> get_lagna_float(2444961.7125,13.08784, 80.27847)
        10.353595502472984
    """
    swe.set_sid_mode(ayanamsha_id)
    lcalc = swe.houses_ex(jd, lat, lon)[1][0] - swe.get_ayanamsa_ut(jd)
    lcalc = lcalc % 360

    if offset == 0:
        return lcalc / 30

    else:
        if (debug):
            print('offset:', offset)
            print('lcalc/30', lcalc / 30)
            print('lcalc/30 + offset = ', lcalc / 30 + offset)

        # The max expected value is somewhere between 2 and -2, with bracketing

        if (lcalc / 30 + offset) >= 3:
            return (lcalc / 30) + offset - 12
        elif (lcalc / 30 + offset) <= -3:
            return (lcalc / 30)
        else:
            return (lcalc / 30) + offset


def get_lagna_data(jd_sunrise, lat, lon, tz_off, ayanamsha_id=swe.SIDM_LAHIRI, debug=False):
    """Returns the lagna data

      Args:
        float jd: The Julian Day at which the lagnam is to be computed
        lat: Latitude of the place where the lagnam is to be computed
        lon: Longitude of the place where the lagnam is to be computed
        offset: Used by internal functions for bracketing

      Returns:
        tuples detailing the end time of each lagna, beginning with the one
        prevailing at sunrise

      Examples:
        >>> get_lagna_data(2458222.5208333335, lat=13.08784, lon=80.27847, tz_off=5.5)
        [(12, 2458222.5214310056), (1, 2458222.596420153), (2, 2458222.6812926503), (3, 2458222.772619788), (4, 2458222.8624254186), (5, 2458222.9478168003), (6, 2458223.0322211445), (7, 2458223.1202004547), (8, 2458223.211770839), (9, 2458223.3000455885), (10, 2458223.3787625884), (11, 2458223.4494649624)]
    """
    lagna_sunrise = 1 + floor(get_lagna_float(jd_sunrise, lat, lon, ayanamsha_id=ayanamsha_id))

    lagna_list = [(x + lagna_sunrise - 1) % 12 + 1 for x in range(12)]

    lbrack = jd_sunrise - 3 / 24
    rbrack = jd_sunrise + 3 / 24
    lagna_data = []

    for lagna in lagna_list:
        # print('---\n', lagna)
        if (debug):
            print('lagna sunrise', get_lagna_float(jd_sunrise, ayanamsha_id=ayanamsha_id))
            print('lbrack', get_lagna_float(lbrack, lat, lon, -lagna, ayanamsha_id=ayanamsha_id))
            print('rbrack', get_lagna_float(rbrack, lat, lon, -lagna, ayanamsha_id=ayanamsha_id))

        lagna_end_time = brentq(get_lagna_float, lbrack, rbrack,
                                args=(lat, lon, -lagna, debug))
        lbrack = lagna_end_time + 1 / 24
        rbrack = lagna_end_time + 3 / 24
        lagna_data.append((lagna, lagna_end_time))
    return lagna_data


def get_solar_month_day(jd_start, city, ayanamsha_id=swe.SIDM_LAHIRI):
    """Compute the solar month and day for a given Julian day

    Computes the solar month and day on the day corresponding to a given
    Julian day

    Args:
      float jd
      city

    Returns:
      int solar_month
      int solar_month_day

    Examples:
      >>> get_solar_month_day(2457023.27, city('Chennai', '13:05:24', \
'80:16:12', 'Asia/Calcutta'))
      (9, 17)
    """

    jd_sunset = swe.rise_trans(jd_start=jd_start, body=swe.SUN, lon=city.longitude,
                               lat=city.latitude, rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]

    solar_month = get_angam(jd_sunset, SOLAR_MONTH, ayanamsha_id=ayanamsha_id)
    target = floor(solar_month) - 1

    jd_masa_transit = brentq(get_angam_float, jd_start - 34, jd_start + 1,
                             args=(SOLAR_MONTH, -target, ayanamsha_id, False))

    jd_next_sunset = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                    lon=city.longitude, lat=city.latitude,
                                    rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]

    jd_next_sunrise = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                     lon=city.longitude, lat=city.latitude,
                                     rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]

    if jd_next_sunset > jd_next_sunrise:
        # Masa begins after sunset and before sunrise
        # Therefore Masa 1 is on the day when the sun rises next
        solar_month_day = floor(jd_sunset - jd_next_sunrise) + 1
    else:
        # Masa has started before sunset
        solar_month_day = round(jd_sunset - jd_next_sunset) + 1

    return (solar_month, solar_month_day)


