import logging
import swisseph as swe
import sys
from math import floor

from sanskrit_data.schema import common
from scipy.optimize import brentq

from jyotisha import names
from jyotisha.custom_transliteration import revjul, tr
from jyotisha.names.init_names_auto import init_names_auto
from jyotisha.zodiac import get_planet_lon

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


NAMES = init_names_auto()
MAX_DAYS_PER_YEAR = 366
MAX_SZ = MAX_DAYS_PER_YEAR + 6  # plus one and minus one are usually necessary
MIN_DAYS_NEXT_ECLIPSE = 25
TITHI = {'id': 'TITHI', 'arc_len': 360.0 / 30.0, 'w_moon': 1, 'w_sun': -1}
TITHI_PADA = {'id': 'TITHI_PADA', 'arc_len': 360.0 / 120.0, 'w_moon': 1, 'w_sun': -1}
NAKSHATRAM = {'id': 'NAKSHATRAM', 'arc_len': 360.0 / 27.0, 'w_moon': 1, 'w_sun': 0}
NAKSHATRA_PADA = {'id': 'NAKSHATRA_PADA', 'arc_len': 360.0 / 108.0, 'w_moon': 1, 'w_sun': 0}
RASHI = {'id': 'RASHI', 'arc_len': 360.0 / 12.0, 'w_moon': 1, 'w_sun': 0}
YOGA = {'id': 'YOGA', 'arc_len': 360.0 / 27.0, 'w_moon': 1, 'w_sun': 1}
KARANAM = {'id': 'KARANAM', 'arc_len': 360.0 / 60.0, 'w_moon': 1, 'w_sun': -1}
SOLAR_MONTH = {'id': 'SOLAR_MONTH', 'arc_len': 360.0 / 12.0, 'w_moon': 0, 'w_sun': 1}
SOLAR_NAKSH = {'id': 'SOLAR_NAKSH', 'arc_len': 360.0 / 27.0, 'w_moon': 0, 'w_sun': 1}
SOLAR_NAKSH_PADA = {'id': 'SOLAR_NAKSH_PADA', 'arc_len': 360.0 / 108.0, 'w_moon': 0, 'w_sun': 1}
TYAJYAM_SPANS_REL = [51, 25, 31, 41, 15, 22, 31, 21, 33,
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


def get_yoga(jd, ayanamsha_id=swe.SIDM_LAHIRI):
    """Returns the yoha prevailing at a given moment

    Yoga is computed based on the longitude of the Moon and longitude of
    the Sun; in addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted (for each).

    Args:
      float jd, the Julian day

    Returns:
      int yoga, where 1 stands for Vishkambha and 27 stands for Vaidhrti

    Examples:
      >>> get_yoga(2444961.7125)
      8
    """

    return get_angam(jd, YOGA, ayanamsha_id=ayanamsha_id)


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
        class, such as TITHI, NAKSHATRAM, YOGA, KARANAM or SOLAR_MONTH

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

    if offset + int(360.0 / arc_len) == 0 and lcalc < arc_len:
        # Angam 1 -- needs different treatment, because of 'discontinuity'
        return (lcalc / arc_len)
    else:
        return (lcalc / arc_len) + offset


def get_planet_next_transit(jd_start, jd_end, planet, ayanamsha_id=swe.SIDM_LAHIRI):
    """Returns the next transit of the given planet e.g. swe.JUPITER

      Args:
        float jd_start, jd_end: The Julian Days between which transits must be computed
        int planet  - e.g. swe.SUN, swe.JUPITER, ...

      Returns:
        List of tuples [(float jd_transit, int old_rashi, int new_rashi)]

      Examples:
      >>> get_planet_next_transit(2457755, 2458120, swe.JUPITER)
      [(2458008.5710764076, 6, 7)]
    """
    swe.set_sid_mode(ayanamsha_id)

    transits = []
    MIN_JUMP = 15  # Random check for a transit every 15 days!
    # Could be tweaked based on planet using a dict?

    curr_L_bracket = jd_start
    curr_R_bracket = jd_start + MIN_JUMP

    while curr_R_bracket <= jd_end:
        L_rashi = floor(get_planet_lon(curr_L_bracket, planet, offset=0,
                                       ayanamsha_id=ayanamsha_id) / 30) + 1
        R_rashi = floor(get_planet_lon(curr_R_bracket, planet, offset=0,
                                       ayanamsha_id=ayanamsha_id) / 30) + 1

        if L_rashi == R_rashi:
            curr_R_bracket += MIN_JUMP
            continue
        else:
            # We have bracketed a transit!
            if L_rashi < R_rashi:
                target = R_rashi
            else:
                # retrograde transit
                target = L_rashi
            try:
                jd_transit = brentq(get_planet_lon, curr_L_bracket, curr_R_bracket,
                                    args=(planet, (-target + 1) * 30, ayanamsha_id))
                transits += [(jd_transit, L_rashi, R_rashi)]
                curr_R_bracket += MIN_JUMP
                curr_L_bracket = jd_transit + MIN_JUMP
            except ValueError:
                sys.stderr.write('Unable to compute transit of planet;\
                                 possibly could not bracket correctly!\n')
                return (None, None, None)

    return transits


def get_angam(jd, angam_type, ayanamsha_id=swe.SIDM_LAHIRI):
    """Returns the angam prevailing at a particular time

      Args:
        float jd: The Julian Day at which the angam is to be computed
        float arc_len: The arc_len for the corresponding angam

      Returns:
        int angam

      Examples:
      >>> get_angam(2444961.7125,NAKSHATRAM)
      16

      >>> get_angam(2444961.7125,TITHI)
      28

      >>> get_angam(2444961.7125,YOGA)
      8

      >>> get_angam(2444961.7125,KARANAM)
      55
    """
    swe.set_sid_mode(ayanamsha_id)

    return int(1 + floor(get_angam_float(jd, angam_type, ayanamsha_id=ayanamsha_id)))


def get_all_angas(jd, ayanamsha_id=swe.SIDM_LAHIRI):
  anga_objects = [TITHI, TITHI_PADA, NAKSHATRAM, NAKSHATRA_PADA, RASHI, SOLAR_MONTH, SOLAR_NAKSH, YOGA, KARANAM]
  angas = list(map(lambda anga_object: get_angam(jd=jd, angam_type=anga_object, ayanamsha_id=ayanamsha_id), anga_objects))
  anga_ids = list(map(lambda anga_obj: anga_obj["id"], anga_objects))
  return dict(list(zip(anga_ids, angas)))


def get_all_angas_x_ayanamshas(jd):
  # swe.SIDM_TRUE_REVATI leads to a segfault.
  ayanamshas = [swe.SIDM_LAHIRI, swe.SIDM_ARYABHATA, swe.SIDM_ARYABHATA_MSUN, swe.SIDM_KRISHNAMURTI, swe.SIDM_JN_BHASIN, swe.SIDM_RAMAN, swe.SIDM_SS_CITRA, swe.SIDM_SS_REVATI, swe.SIDM_SURYASIDDHANTA, swe.SIDM_SURYASIDDHANTA_MSUN, swe.SIDM_USHASHASHI, swe.SIDM_YUKTESHWAR, swe.SIDM_LAHIRI, names.SIDM_TRUE_MULA, names.SIDM_TRUE_PUSHYA]

  ayanamsha_names = list(map(lambda ayanamsha: names.get_ayanamsha_name(ayanamsha), ayanamshas))
  return dict(zip(ayanamsha_names, map(lambda ayanamsha_id: get_all_angas(jd=jd, ayanamsha_id=ayanamsha_id), ayanamshas)))


def print_angas_x_ayanamshas(jd):
  anga_x_ayanamsha = get_all_angas_x_ayanamshas(jd=jd)
  import pandas
  angas_df = pandas.DataFrame(anga_x_ayanamsha)
  print(angas_df.to_csv(sep="\t"))


def get_angam_span(jd1, jd2, angam_type, target, ayanamsha_id=swe.SIDM_LAHIRI, debug=False):
    """Computes angam spans for angams such as tithi, nakshatram, yoga
        and karanam.

        Args:
          jd1: return the first span that starts after this date
          jd2: return the first span that ends before this date
          angam_type: TITHI, NAKSHATRAM, YOGA, KARANAM, SOLAR_MONTH, SOLAR_NAKSH

        Returns:
          tuple: A tuple of start and end times that lies within jd1 and jd2
    """

    angam_start = angam_end = None

    if debug:
      logging.debug(get_angam(jd1, angam_type, ayanamsha_id=ayanamsha_id))
      logging.debug(get_angam(jd2, angam_type, ayanamsha_id=ayanamsha_id))

    num_angas = int(360.0 / angam_type['arc_len'])

    jd_bracket_L = jd1
    jd_bracket_R = jd2

    h = 0.5   # Min Step for moving

    jd_now = jd1
    while jd_now < jd2 and angam_start is None:
        angam_now = get_angam(jd_now, angam_type, ayanamsha_id=ayanamsha_id)

        if debug:
            logging.debug((jd_now, revjul(jd_now), angam_now, get_angam_float(jd_now, angam_type, ayanamsha_id=ayanamsha_id)))
        if angam_now < target or (target == 1 and angam_now == num_angas):
            if debug:
                logging.debug(('jd_bracket_L ', jd_now))
            jd_bracket_L = jd_now
        if angam_now == target:
            try:
              angam_start = brentq(get_angam_float, jd_bracket_L, jd_now,
                                   args=(angam_type, -target + 1, ayanamsha_id, False))
            except ValueError:
              logging.error('Unable to bracket %s->%f between jd = (%f, %f), starting with (%f, %f)' % (str(angam_type), -target + 1, jd_bracket_L, jd_now, jd1, jd2))
              angam_start = None
            if debug:
                logging.debug(('angam_start', angam_start))
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
            logging.debug((jd_now, revjul(jd_now), angam_now, get_angam_float(jd_now, angam_type, ayanamsha_id=ayanamsha_id)))
        if target == num_angas:
            # Wait till we land at the next anga!
            if angam_now == 1:
                jd_bracket_R = jd_now
                if debug:
                    logging.debug(('jd_bracket_R ', jd_now))
                break
        else:
            if angam_now > target:
                jd_bracket_R = jd_now
                if debug:
                    logging.debug(('jd_bracket_R ', jd_now))
                break
        jd_now += h

    try:
        angam_end = brentq(get_angam_float, angam_start, jd_bracket_R,
                           args=(angam_type, -target, ayanamsha_id, False))
    except ValueError:
        logging.error('Unable to compute angam_end (%s->%d); possibly could not bracket correctly!\n' % (str(angam_type), target))

    if debug:
        logging.debug(('angam_end', angam_end))

    return (angam_start, angam_end)


def get_angam_data(jd_sunrise, jd_sunrise_tmrw, angam_type, ayanamsha_id=swe.SIDM_LAHIRI):
    """Computes angam data for angams such as tithi, nakshatram, yoga
    and karanam.

    Args:
      angam_type: TITHI, NAKSHATRAM, YOGA, KARANAM, SOLAR_MONTH, SOLAR_NAKSH


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
      >>> get_angam_data(2444961.54042,2444962.54076,YOGA)
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
            try:
              t_act = brentq(get_angam_float, x0 - TDELTA, x0 + TDELTA,
                             args=(angam_type, -target, ayanamsha_id, False))
            except ValueError:
              logging.warning('Unable to bracket! Using approximate t_end itself.')
              logging.warning(locals())
              t_act = approx_end
            angams_list.extend([((angam_now + i - 1) % num_angas + 1, t_act)])
    return angams_list


def get_ekadashi_name(paksha, lmonth):
    """Return the name of an ekadashi
    """
    if paksha == 'shukla':
        if lmonth == int(lmonth):
            return '%s-EkAdazI' % NAMES['SHUKLA_EKADASHI_NAMES']['hk'][lmonth]
        else:
            # adhika mAsam
            return '%s-EkAdazI' % NAMES['SHUKLA_EKADASHI_NAMES']['hk'][13]
    elif paksha == 'krishna':
        if lmonth == int(lmonth):
            return '%s-EkAdazI' % NAMES['KRISHNA_EKADASHI_NAMES']['hk'][lmonth]
        else:
            # adhika mAsam
            return '%s-EkAdazI' % NAMES['KRISHNA_EKADASHI_NAMES']['hk'][13]


def get_chandra_masa(month, NAMES, script, visarga=True):
    if visarga:
      if month == int(month):
          return NAMES['CHANDRA_MASA_NAMES'][script][month]
      else:
          return '%s-(%s)' % (NAMES['CHANDRA_MASA_NAMES'][script][int(month) + 1], tr('adhikaH', script, titled=False))
    else:
      if month == int(month):
          return NAMES['CHANDRA_MASA_NAMES'][script][month][:-1]
      else:
          return '%s-(%s)' % (NAMES['CHANDRA_MASA_NAMES'][script][int(month) + 1][:-1], tr('adhika', script, titled=False))


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


def get_kaalas(start_span, end_span, part_start, num_parts):
    """Compute kaalas in a given span with specified fractions

    Args:
      :param start_span float (jd)
      :param end_span float (jd)
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


def sanitize_time(year_in, month_in, day_in, hour_in, minute_in, second_in):
    (year, month, day, hour, minute, second) = (year_in, month_in, day_in, hour_in, minute_in, second_in)
    if second >= 60:
        minute = minute + second / 60
        second = second % 60
    if minute >= 60:
        hour = hour + minute / 60
        minute = minute % 60
    if hour >= 24:
        day = day + hour / 24
        hour = hour % 24
    from calendar import monthrange
    (_, final_day) = monthrange(year, month)
    if day > final_day:
        assert day == final_day + 1, "range not supported by this function"
        day = 1
        month = month + 1
    if month >= 13:
        year = year + (month - 1) / 12
        month = ((month - 1) % 12) + 1
    return (year, month, day, hour, minute, second)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
