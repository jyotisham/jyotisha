import logging
import swisseph as swe
import sys
from math import floor

from scipy.optimize import brentq

from jyotisha import names
from jyotisha.custom_transliteration import revjul, tr
from jyotisha.names.init_names_auto import init_names_auto

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)



NAMES = init_names_auto()
MAX_DAYS_PER_YEAR = 366
MAX_SZ = MAX_DAYS_PER_YEAR + 3  # plus one and minus one are usually necessary
MIN_DAYS_NEXT_ECLIPSE = 25
TITHI = {'id': 'TITHI', 'arc_len': 360.0 / 30.0,  'w_moon': 1, 'w_sun': -1}
TITHI_PADA = {'id': 'TITHI_PADA', 'arc_len': 360.0 / 120.0, 'w_moon': 1, 'w_sun': -1}
NAKSHATRAM = {'id': 'NAKSHATRAM', 'arc_len': 360.0 / 27.0,  'w_moon': 1, 'w_sun':  0}
NAKSHATRA_PADA = {'id': 'NAKSHATRA_PADA', 'arc_len': 360.0 / 108.0, 'w_moon': 1, 'w_sun':  0}
RASHI = {'id': 'RASHI', 'arc_len': 360.0 / 12.0,  'w_moon': 1, 'w_sun':  0}
YOGAM = {'id': 'YOGAM', 'arc_len': 360.0 / 27.0,  'w_moon': 1, 'w_sun':  1}
KARANAM = {'id': 'KARANAM', 'arc_len': 360.0 / 60.0,  'w_moon': 1, 'w_sun': -1}
SOLAR_MONTH = {'id': 'SOLAR_MONTH', 'arc_len': 360.0 / 12.0,  'w_moon': 0, 'w_sun':  1}
SOLAR_NAKSH = {'id': 'SOLAR_NAKSH', 'arc_len': 360.0 / 27.0,  'w_moon': 0, 'w_sun':  1}


class Time(object):

    """This  class is a time class with methods for printing, conversion etc.
    """

    def __init__(self, t):
        if type(t) == float or type(t) == int:
            self.t = t
        else:
            raise(TypeError('Input to time class must be int or float!'))

    def toString(self, default_suffix='', format='hh:mm'):
        secs = round(self.t * 3600)  # round to nearest second
        hour = secs // 3600
        secs = secs % 3600

        if hour >= 24:
            hour -= 24
            suffix = '(+1)'
        else:
            suffix = default_suffix

        minute = secs // 60
        secs = secs % 60
        second = secs

        if format == 'hh:mm':
            return '%02d:%02d%s' % (hour, minute, suffix)
        elif format == 'hh:mm:ss':
            return '%02d:%02d:%02d%s' % (hour, minute, second, suffix)
        else:
            """Thrown an exception, for unknown format"""

    def __str__(self):
        return self.toString(format='hh:mm:ss')


def get_nakshatram(jd, ayanamsha_id=swe.SIDM_LAHIRI):
    """Returns the nakshatram prevailing at a given moment

    Nakshatram is computed based on the longitude of the Moon; in
    addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted.

    Args:
      float jd, the Julian day

    Returns:
      int nakShatram, where 1 stands for Ashwini, ..., 14 stands
      for Chitra, ..., 27 stands for Revati

    Examples:
      >>> get_nakshatram(2444961.7125)
      16
    """

    return get_angam(jd, NAKSHATRAM, ayanamsha_id=ayanamsha_id)


def get_solar_rashi(jd, ayanamsha_id=swe.SIDM_LAHIRI):
    """Returns the solar rashi prevailing at a given moment

    Solar month is computed based on the longitude of the sun; in
    addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted.

    Args:
      float jd, the Julian day

    Returns:
      int rashi, where 1 stands for mESa, ..., 12 stands for mIna

    Examples:
      >>> get_solar_rashi(2444961.7125)
      9
    """

    return get_angam(jd, SOLAR_MONTH, ayanamsha_id=ayanamsha_id)


def get_angam_float(jd, angam_type, offset=0, ayanamsha_id=swe.SIDM_LAHIRI, debug=False):
    """Returns the angam

      Args:
        float jd: The Julian Day at which the angam is to be computed
        angam_type: One of the pre-defined constants in the panchangam
        class, such as TITHI, NAKSHATRAM, YOGAM, KARANAM or SOLAR_MONTH

      Returns:
        float angam

      Examples:
        >>> get_angam_float(2444961.7125,NAKSHATRAM)
        15.967801358055189
    """
    swe.set_sid_mode(ayanamsha_id)
    w_moon = angam_type['w_moon']
    w_sun = angam_type['w_sun']
    arc_len = angam_type['arc_len']

    lcalc = 0  # computing weighted longitudes
    if debug:
        logging.debug('## get_angam_float(): jd=%f', jd)
        logging.debug("Ayanamsha: %f", swe.get_ayanamsa(jd))

    #  Get the lunar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_moon != 0:
        lmoon = (swe.calc_ut(jd, swe.MOON)[0] - swe.get_ayanamsa(jd)) % 360
        if (debug):
            logging.debug("Moon longitude: %f", swe.calc_ut(jd, swe.MOON)[0])
            logging.debug('## get_angam_float(): lmoon=%f', lmoon)
        lcalc += w_moon * lmoon

    #  Get the solar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_sun != 0:
        lsun = (swe.calc_ut(jd, swe.SUN)[0] - swe.get_ayanamsa(jd)) % 360
        if(debug):
            logging.debug('## get_angam_float(): lsun=%f', lsun)
        lcalc += w_sun * lsun

    if debug:
        logging.debug('## get_angam_float(): lcalc=%f', lcalc)

    lcalc = lcalc % 360

    if debug:
        logging.debug('## get_angam_float(): lcalc %% 360=%f', lcalc)
        logging.debug("offset: %f", offset)
        logging.debug(offset + int(360.0 / arc_len))
    if offset + int(360.0 / arc_len) == 0 and lcalc + offset >= 0:
        return (lcalc / arc_len)
    else:
        return (lcalc / arc_len) + offset


def get_nirayana_sun_lon(jd, offset=0, debug=False):
    """Returns the nirayana longitude of the sun

      Args:
        float jd: The Julian Day at which the angam is to be computed

      Returns:
        float longitude

      Examples:
    """
    lsun = (swe.calc_ut(jd, swe.SUN)[0]) % 360

    if debug:
        print('## get_angam_float(): lsun (nirayana) =', lsun)

    return lsun + offset


def get_angam(jd, angam_type, ayanamsha_id=swe.SIDM_LAHIRI):
    """Returns the angam prevailing at a particular time

      Args:
        float jd: The Julian Day at which the angam is to be computed
        float arc_len: The arc_len for the corresponding angam
        w_moon: The multiplier for moon's longitude
        w_sun: The multiplier for sun's longitude

      Returns:
        int angam

      Examples:
      >>> get_angam(2444961.7125,NAKSHATRAM)
      16

      >>> get_angam(2444961.7125,TITHI)
      28

      >>> get_angam(2444961.7125,YOGAM)
      8

      >>> get_angam(2444961.7125,KARANAM)
      55
    """
    swe.set_sid_mode(ayanamsha_id)

    return int(1 + floor(get_angam_float(jd, angam_type, ayanamsha_id=ayanamsha_id)))


def get_all_angas(jd, ayanamsha_id=swe.SIDM_LAHIRI):
  anga_objects = [TITHI, TITHI_PADA, NAKSHATRAM, NAKSHATRA_PADA, RASHI, SOLAR_MONTH, SOLAR_NAKSH, YOGAM, KARANAM]
  angas = list(map(lambda anga_object: get_angam(jd=jd, angam_type=anga_object, ayanamsha_id=ayanamsha_id), anga_objects))
  anga_ids = list(map(lambda anga_obj: anga_obj["id"], anga_objects))
  return dict(list(zip(anga_ids, angas)))


def get_all_angas_x_ayanamshas(jd):
  # swe.SIDM_TRUE_REVATI leads to a segfault.
  ayanamshas = [swe.SIDM_LAHIRI, swe.SIDM_ARYABHATA, swe.SIDM_ARYABHATA_MSUN, swe.SIDM_KRISHNAMURTI, swe.SIDM_JN_BHASIN, swe.SIDM_RAMAN, swe.SIDM_SS_CITRA, swe.SIDM_SS_REVATI, swe.SIDM_SURYASIDDHANTA, swe.SIDM_SURYASIDDHANTA_MSUN, swe.SIDM_USHASHASHI, swe.SIDM_YUKTESHWAR, swe.SIDM_TRUE_CITRA, names.SIDM_TRUE_MULA, names.SIDM_TRUE_PUSHYA]

  ayanamsha_names = list(map(lambda ayanamsha: names.get_ayanamsha_name(ayanamsha), ayanamshas))
  return dict(zip(ayanamsha_names, map(lambda ayanamsha_id: get_all_angas(jd=jd, ayanamsha_id=ayanamsha_id), ayanamshas)))


def print_angas_x_ayanamshas(jd):
  anga_x_ayanamsha = get_all_angas_x_ayanamshas(jd=jd)
  import pandas
  angas_df = pandas.DataFrame(anga_x_ayanamsha)
  print(angas_df.to_csv(sep="\t"))


def get_angam_span(jd1, jd2, angam_type, target, ayanamsha_id=swe.SIDM_LAHIRI, debug=False):
    """Computes angam spans for angams such as tithi, nakshatram, yogam
        and karanam.

        Args:
          jd1: return all spans that start after this date
          jd2: return all spans that end before this date
          angam_type: TITHI, NAKSHATRAM, YOGAM, KARANAM, SOLAR_MONTH, SOLAR_NAKSH

        Returns:
          list: A list comprising tuples of start and end times that lie within
            jd1 and jd2
    """

    angam_start = angam_end = None

    num_angas = int(360.0 / angam_type['arc_len'])

    jd_bracket_L = jd1
    jd_bracket_R = jd2

    h = 0.5   # Min Step for moving

    jd_now = jd1
    while jd_now < jd2 and angam_start is None:
        angam_now = get_angam(jd_now, angam_type, ayanamsha_id=ayanamsha_id)

        if debug:
            print('%%', jd_now, revjul(jd_now), angam_now, get_angam_float(jd_now, angam_type, ayanamsha_id=ayanamsha_id))
        if angam_now < target:
            if debug:
                print('%% jd_bracket_L ', jd_now)
            jd_bracket_L = jd_now
        if angam_now == target:
            angam_start = brentq(get_angam_float, jd_bracket_L, jd_now,
                                 args=(angam_type, -target + 1, ayanamsha_id, False))
            if debug:
                print('%% angam_start', angam_start)
        # if angam_now > target and angam_start is not None:
        #     angam_end = brentq(get_angam_float, angam_start, jd_now,
        #                        args=(angam_type, -target, False))
        jd_now += h

    if angam_start is None:
        return (None, None)  # If it doesn't start, we don't care if it ends!
    jd_now = angam_start

    while jd_now < jd2 and angam_end is None:
        angam_now = get_angam(jd_now, angam_type, ayanamsha_id=ayanamsha_id)

        if debug:
            print('%%#', jd_now, revjul(jd_now), angam_now, get_angam_float(jd_now, angam_type, ayanamsha_id=ayanamsha_id))
        if target == num_angas:
            # Wait till we land at the next anga!
            if angam_now == 1:
                jd_bracket_R = jd_now
                if debug:
                    print('%%# jd_bracket_R ', jd_now)
                break
        else:
            if angam_now > target:
                jd_bracket_R = jd_now
                if debug:
                    print('%%! jd_bracket_R ', jd_now)
                break
        jd_now += h

    try:
        angam_end = brentq(get_angam_float, angam_start, jd_bracket_R,
                           args=(angam_type, -target, ayanamsha_id, False))
    except:
        sys.stderr.write('Unable to compute angam_end (%s->%d); possibly could not bracket correctly!\n' % (str(angam_type), target))

    if debug:
        print('%% angam_end', angam_end)

    return (angam_start, angam_end)


def get_angam_data(jd_sunrise, jd_sunrise_tmrw, angam_type, ayanamsha_id=swe.SIDM_LAHIRI):
    """Computes angam data for angams such as tithi, nakshatram, yogam
    and karanam.

    Args:
      angam_type: TITHI, NAKSHATRAM, YOGAM, KARANAM, SOLAR_MONTH, SOLAR_NAKSH


    Returns:
      tuple: A tuple comprising
        angam_sunrise: The angam that prevails as sunrise
        angam_data: a list of (int, float) tuples detailing the angams
        for the day and their end-times (Julian day)

    Examples:
      >>> get_angam_data(2444961.54042,2444962.54076,TITHI)
      [(27, 2444961.599213231)]
      >>> get_angam_data(2444961.54042,2444962.54076,NAKSHATRAM)
      [(16, 2444961.7487953394)]
      >>> get_angam_data(2444961.54042,2444962.54076,YOGAM)
      [(8, 2444962.1861976916)]
      >>> get_angam_data(2444961.54042,2444962.54076,KARANAM)
      [(54, 2444961.599213231), (55, 2444962.15444546)]
    """
    swe.set_sid_mode(ayanamsha_id)

    w_moon = angam_type['w_moon']
    w_sun = angam_type['w_sun']
    arc_len = angam_type['arc_len']

    num_angas = int(360.0 / arc_len)

    # Compute angam details
    angam_now = get_angam(jd_sunrise, angam_type, ayanamsha_id=ayanamsha_id)
    angam_tmrw = get_angam(jd_sunrise_tmrw, angam_type, ayanamsha_id=ayanamsha_id)

    angams_list = []

    num_angas_today = (angam_tmrw - angam_now) % num_angas

    if num_angas_today == 0:
        # The angam does not change until sunrise tomorrow
        return [(angam_now, None)]
    else:
        lmoon = (swe.calc_ut(jd_sunrise, swe.MOON)[0] - swe.get_ayanamsa(jd_sunrise)) % 360

        lsun = (swe.calc_ut(jd_sunrise, swe.SUN)[0] - swe.get_ayanamsa(jd_sunrise)) % 360

        lmoon_tmrw = (swe.calc_ut(jd_sunrise_tmrw, swe.MOON)[0] -
                      swe.get_ayanamsa(jd_sunrise_tmrw)) % 360

        lsun_tmrw = (swe.calc_ut(jd_sunrise_tmrw, swe.SUN)[0] -
                     swe.get_ayanamsa(jd_sunrise_tmrw)) % 360

        for i in range(num_angas_today):
            angam_remaining = arc_len * (i + 1) - (((lmoon * w_moon +
                                                     lsun * w_sun) % 360) % arc_len)

            # First compute approximate end time by essentially assuming
            # the speed of the moon and the sun to be constant
            # throughout the day. Therefore, angam_remaining is computed
            # just based on the difference in longitudes for sun and
            # moon today and tomorrow.
            approx_end = jd_sunrise + angam_remaining / (((lmoon_tmrw - lmoon) % 360) * w_moon +
                                                         ((lsun_tmrw - lsun) % 360) * w_sun)

            # Initial guess value for the exact end time of the angam
            x0 = approx_end

            # What is the target (next) angam? It is needed to be passed
            # to get_angam_float for zero-finding. If the target angam
            # is say, 12, then we need to subtract 12 from the value
            # returned by get_angam_float, so that this function can be
            # passed as is to a zero-finding method like brentq or
            # newton. Since we have a good x0 guess, it is easy to
            # bracket the function in an interval where the function
            # changes sign. Therefore, brenth can be used, as suggested
            # in the scipy documentation.
            target = (angam_now + i - 1) % num_angas + 1

            # Approximate error in calculation of end time -- arbitrary
            # used to bracket the root, for brenth
            TDELTA = 0.05
            t_act = brentq(get_angam_float, x0 - TDELTA, x0 + TDELTA,
                           args=(angam_type, -target, ayanamsha_id, False))
            angams_list.extend([((angam_now + i - 1) % num_angas + 1, t_act)])
    return angams_list


def get_ekadashi_name(paksha, lmonth):
    """Return the name of an ekadashi
    """
    if paksha == 'shukla':
        if lmonth == int(lmonth):
            return '%s~EkAdazI' % NAMES['SHUKLA_EKADASHI']['hk'][lmonth]
        else:
            # adhika mAsam
            return '%s~EkAdazI' % NAMES['SHUKLA_EKADASHI']['hk'][13]
    elif paksha == 'krishna':
        if lmonth == int(lmonth):
            return '%s~EkAdazI' % NAMES['KRISHNA_EKADASHI']['hk'][lmonth]
        else:
            # adhika mAsam
            return '%s~EkAdazI' % NAMES['KRISHNA_EKADASHI']['hk'][13]


def get_chandra_masa(month, NAMES, script):
    if month == int(month):
        return NAMES['CHANDRA_MASA'][script][month]
    else:
        return '%s~(%s)' % (NAMES['CHANDRA_MASA'][script][int(month) + 1], tr('adhika', script))


def get_tithi(jd, ayanamsha_id=swe.SIDM_LAHIRI):
    """Returns the tithi prevailing at a given moment

    Tithi is computed as the difference in the longitudes of the moon
    and sun at any given point of time. Therefore, even the ayanamsha
    does not matter, as it gets cancelled out.

    Args:
      float jd, the Julian day

    Returns:
      int tithi, where 1 stands for ShuklapakshaPrathama, ..., 15 stands
      for Paurnamasi, ..., 23 stands for KrishnapakshaAshtami, 30 stands
      for Amavasya

    Examples:
      >>> get_tithi(2444961.7125)
      28
    """

    return get_angam(jd, TITHI, ayanamsha_id=ayanamsha_id)


def get_kalas(start_span, end_span, part_start, num_parts):
    """Compute kalas in a given span with specified fractions

    Args:
      float (jd) start_span
      float (jd) end_span
      int part_start
      int num_parts

    Returns:
       tuple (start_time_jd, end_time_jd)

    Examples:

    """
    start_fraction = part_start / num_parts
    end_fraction = (part_start + 1) / num_parts

    start_time = start_span + (end_span - start_span) * start_fraction
    end_time = start_span + (end_span - start_span) * end_fraction

    return (start_time, end_time)


if __name__ == '__main__':
  # time = swe.utc_to_jd(year=1982, month=2, day=18, hour=11, minutes=10, seconds=0, flag=1)[0]
  time = swe.utc_to_jd(year=2015, month=9, day=17, hour=15, minutes=16, seconds=0, flag=1)[0]
  # time = swe.utc_to_jd(year=1986, month=8, day=24, hour=11, minutes=54, seconds=0, flag=1)[0]
  logging.info(time)
  print_angas_x_ayanamshas(jd=time)
