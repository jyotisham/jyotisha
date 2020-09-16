import logging
from math import floor

import numpy
import swisseph as swe
from astropy.time import Time
from scipy.optimize import brentq

from jyotisha.panchangam.temporal.body import Graha

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class Ayanamsha(object):
    CHITRA_AT_180 = "CHITRA_AT_180"
    
    def __init__(self, ayanamsha_id):
        self.ayanamsha_id = ayanamsha_id
    
    def get_offset(self, jd):
        if self.ayanamsha_id == Ayanamsha.CHITRA_AT_180:
            # TODO: The below fails due to https://github.com/astrorigin/pyswisseph/issues/35
            from jyotisha.panchangam.temporal import body
            return (body.get_star_longitude(star="Spica", jd=jd)-180)
            # swe.set_sid_mode(swe.SIDM_LAHIRI)
            # return swe.get_ayanamsa_ut(jd)
        raise Exception("Bad ayamasha_id")


class NakshatraDivision(object):
  """Nakshatra division at a certain time, according to a certain ayanaamsha."""

  def __init__(self, julday, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
    self.ayanamsha_id = ayanamsha_id
    
    self.set_time(julday=julday)

  # noinspection PyAttributeOutsideInit
  def set_time(self, julday):
    self.julday = julday
    self.right_boundaries = ((numpy.arange(27) + 1) * (360.0 / 27.0) + Ayanamsha(self.ayanamsha_id).get_offset(julday)) % 360

  def get_nakshatra(self, body, julday=None):
    if julday is not None:
      self.set_time(julday=julday)
    logging.debug(Ayanamsha(self.ayanamsha_id).get_offset(self.julday))
    return ((Graha(body).get_longitude(self.julday) - Ayanamsha(self.ayanamsha_id).get_offset(self.julday)) % 360) / (360.0 / 27.0)

  def __str__(self):
    return str(self.__dict__)

  def get_equatorial_boundary_coordinates(self):
    """Get equatorial coordinates for the points where the ecliptic nakShatra boundary longitude intersects the ecliptic."""
    equatorial_boundary_coordinates = [ecliptic_to_equatorial(longitude=longitude, latitude=0) for longitude in self.right_boundaries]
    return equatorial_boundary_coordinates

  def get_stellarium_nakshatra_boundaries(self):
    equatorial_boundary_coordinates_with_ra = self.get_equatorial_boundary_coordinates()
    ecliptic_north_pole_with_ra = ecliptic_to_equatorial(longitude=20, latitude=90)
    # logging.debug(ecliptic_north_pole_with_ra)
    ecliptic_south_pole_with_ra = ecliptic_to_equatorial(longitude=20, latitude=-90)
    # logging.debug(ecliptic_south_pole_with_ra)
    for index, (boundary_ra, boundary_declination) in enumerate(equatorial_boundary_coordinates_with_ra):
      print(
        '3 %(north_pole_ra)f %(north_pole_dec)f %(boundary_ra)f %(boundary_declination)f %(south_pole_ra)f %(south_pole_dec)f 2 N%(sector_id_1)02d N%(sector_id_2)02d' % dict(
          north_pole_ra=ecliptic_north_pole_with_ra[0],
          north_pole_dec=ecliptic_north_pole_with_ra[1],
          boundary_ra=boundary_ra,
          boundary_declination=boundary_declination,
          south_pole_ra=ecliptic_south_pole_with_ra[0],
          south_pole_dec=ecliptic_south_pole_with_ra[1],
          sector_id_1=(index % 27 + 1),
          sector_id_2=((index + 1) % 27 + 1)
        ))


def get_nirayana_sun_lon(jd, offset=0, debug=False):
    """Returns the nirayana longitude of the sun

      Args:
        float jd: The Julian Day at which the angam is to be computed

      Returns:
        float longitude

      Examples:
    """
    lsun = (Graha(Graha.SUN).get_longitude(jd)) % 360

    if debug:
        print('## get_angam_float(): lsun (nirayana) =', lsun)

    if offset + 360 == 0 and lsun < 30:
        # Angam 1 -- needs different treatment, because of 'discontinuity'
        return lsun
    else:
        return lsun + offset



def longitudeToRightAscension(longitude):
    return (360 - longitude) / 360 * 24


def ecliptic_to_equatorial(longitude, latitude):
    coordinates = swe.cotrans(lon=longitude, lat=latitude, dist=9999999, obliquity=23.437404)
    # swe.cotrans returns the right ascension longitude in degrees, rather than hours.
    return (
        longitudeToRightAscension(coordinates[0]), coordinates[1])


if __name__ == '__main__':
    # lahiri_nakshatra_division = NakshatraDivision(julday=temporal.utc_to_jd(year=2017, month=8, day=19, hour=11, minutes=10, seconds=0, flag=1)[0])
    import temporal
    lahiri_nakshatra_division = NakshatraDivision(
        julday=temporal.utc_gregorian_to_jd(year=1982, month=2, day=19, fractional_hour=11, minutes=10, seconds=0, flag=1)[0])
    logging.info(lahiri_nakshatra_division.get_nakshatra(body=Graha.MOON))
    # logging.info(lahiri_nakshatra_division)
    lahiri_nakshatra_division.get_stellarium_nakshatra_boundaries()


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


def get_angam_float(jd, angam_type, offset=0, ayanamsha_id=Ayanamsha.CHITRA_AT_180, debug=False):
    """Returns the angam

      Args:
        :param jd: float: The Julian Day at which the angam is to be computed
        :param angam_type: One of the pre-defined tuple-valued constants in the panchangam
        class, such as TITHI, NAKSHATRAM, YOGA, KARANAM or SOLAR_MONTH
        :param offset: 
        :param ayanamsha_id: 
        :param debug: Unused

      Returns:
        float angam

      Examples:
        >>> get_angam_float(2444961.7125,NAKSHATRAM)
        15.967801358055189
        
    """
    
    w_moon = angam_type['w_moon']
    w_sun = angam_type['w_sun']
    arc_len = angam_type['arc_len']

    lcalc = 0  # computing offset longitudes

    #  Get the lunar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_moon != 0:
        lmoon = Graha(Graha.MOON).get_longitude_offset(jd, offset=0, ayanamsha_id=ayanamsha_id)
        lcalc += w_moon * lmoon

    #  Get the solar longitude, starting at the ayanaamsha point in the ecliptic.
    if w_sun != 0:
        lsun = Graha(Graha.SUN).get_longitude_offset(jd, offset=0, ayanamsha_id=ayanamsha_id)
        lcalc += w_sun * lsun

    lcalc = lcalc % 360

    if offset + int(360.0 / arc_len) == 0 and lcalc < arc_len:
        # Angam 1 -- needs different treatment, because of 'discontinuity'
        return (lcalc / arc_len)
    else:
        return (lcalc / arc_len) + offset


def get_angam(jd, angam_type, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
    """Returns the angam prevailing at a particular time

      Args:
        float jd: The Julian Day at which the angam is to be computed
        float arc_len: The arc_len for the corresponding angam

      Returns:
        int angam
    """
    

    return int(1 + floor(get_angam_float(jd, angam_type, ayanamsha_id=ayanamsha_id)))


def get_all_angas(jd, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
  anga_objects = [TITHI, TITHI_PADA, NAKSHATRAM, NAKSHATRA_PADA, RASHI, SOLAR_MONTH, SOLAR_NAKSH, YOGA, KARANAM]
  angas = list(map(lambda anga_object: get_angam(jd=jd, angam_type=anga_object, ayanamsha_id=ayanamsha_id), anga_objects))
  anga_ids = list(map(lambda anga_obj: anga_obj["id"], anga_objects))
  return dict(list(zip(anga_ids, angas)))


def get_angam_span(jd1, jd2, angam_type, target, ayanamsha_id=Ayanamsha.CHITRA_AT_180, debug=False):
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
            logging.debug((jd_now, Time(jd_now, "jd").to_value('iso'), angam_now, get_angam_float(jd_now, angam_type, ayanamsha_id=ayanamsha_id)))
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
            logging.debug((jd_now, Time(jd_now, "jd").to_value('iso'), angam_now, get_angam_float(jd_now, angam_type, ayanamsha_id=ayanamsha_id)))
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


def get_angam_data(jd_sunrise, jd_sunrise_tmrw, angam_type, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
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
        lmoon = (Graha(Graha.MOON).get_longitude(jd_sunrise) - Ayanamsha(ayanamsha_id).get_offset(jd_sunrise)) % 360

        lsun = (Graha(Graha.SUN).get_longitude(jd_sunrise) - Ayanamsha(ayanamsha_id).get_offset(jd_sunrise)) % 360

        lmoon_tmrw = (Graha(Graha.MOON).get_longitude(jd_sunrise_tmrw) -
                      Ayanamsha(ayanamsha_id).get_offset(jd_sunrise_tmrw)) % 360

        lsun_tmrw = (Graha(Graha.SUN).get_longitude(jd_sunrise_tmrw) -
                     Ayanamsha(ayanamsha_id).get_offset(jd_sunrise_tmrw)) % 360

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


def get_tithi(jd, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
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

def get_nakshatram(jd, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
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


def get_yoga(jd, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
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


def get_solar_rashi(jd, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
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


