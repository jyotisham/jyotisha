import logging

from jyotisha.panchangam import temporal

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def test_sanitize_time():
    assert temporal.sanitize_time(2018, 11, 11, 10, 8, 60) == (2018, 11, 11, 10, 9, 00)
    assert temporal.sanitize_time(2018, 12, 31, 23, 60, 00) == (2019, 1, 1, 00, 00, 00)


def test_ayanamsha_api():
    import swisseph as swe
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
    # jd = city.local_time_to_julian_day(year=2018, month=11, day=11, hours=6, minutes=0, seconds=0)
    assert swe.get_ayanamsa(2458434.083333251) == 24.120535828308334


def test_jd_to_utc():
    assert temporal.jd_to_utc(2458434.083333251) == [2018, 11, 11, 13.99999802559611]
    

def test_utc_to_jd():
    assert abs(temporal.utc_to_jd(2018, 11, 11, 13.99999802559611) - 2458434.083333251) < .001