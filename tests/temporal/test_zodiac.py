import logging

from jyotisha.panchangam.temporal import zodiac
from jyotisha.panchangam.temporal.zodiac import NakshatraDivision, Ayanamsha, AngaSpan


def test_get_ayanamsha():
    ayanamsha = zodiac.Ayanamsha(ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
    assert ayanamsha.get_offset(2458434.083333251) == 24.094859396693067


def disabled_test_swe_ayanamsha_api():
    import swisseph as swe
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
    # jd = city.local_time_to_julian_day(year=2018, month=11, day=11, hours=6, minutes=0, seconds=0)
    assert swe.get_ayanamsa_ut(2458434.083333251) == 24.120535828308334


def test_get_angam():
    nd = NakshatraDivision(2444961.7125, ayanamsha_id=Ayanamsha.CHITRA_AT_180)
    assert nd.get_angam(zodiac.NAKSHATRAM) == 16
    assert nd.get_angam(zodiac.TITHI) == 28
    assert nd.get_angam(zodiac.YOGA) == 8
    assert nd.get_angam(zodiac.KARANAM) == 55
    assert nd.get_solar_rashi() == 9


def test_get_angam_data():
    assert zodiac.get_angam_data(2444961.54042,2444962.54076, zodiac.TITHI, ayanamsha_id=Ayanamsha.CHITRA_AT_180) == [(27, 2444961.5992132244)]
    assert zodiac.get_angam_data(2444961.54042,2444962.54076, zodiac.NAKSHATRAM, ayanamsha_id=Ayanamsha.CHITRA_AT_180) == [(16, 2444961.746925843)]
    assert zodiac.get_angam_data(2444961.54042,2444962.54076, zodiac.YOGA, ayanamsha_id=Ayanamsha.CHITRA_AT_180) == [(8, 2444962.18276057)]
    assert zodiac.get_angam_data(2444961.54042,2444962.54076, zodiac.KARANAM, ayanamsha_id=Ayanamsha.CHITRA_AT_180) == [(54, 2444961.5992132244), (55, 2444962.1544454526)]

def test_get_angam_span():
    assert AngaSpan.find(jd1=2444959.54042,jd2=2444963.54076, angam_type=zodiac.TITHI, target_anga_id=27, ayanamsha_id=Ayanamsha.CHITRA_AT_180).to_tuple() == (2444960.4924699212, 2444961.599213224)
