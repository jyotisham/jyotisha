from jyotisha.panchaanga.temporal import zodiac, time
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, Ayanamsha, AngaType, AngaSpanFinder


def test_get_ayanaamsha():
  ayanaamsha = zodiac.Ayanamsha.singleton(ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
  assert ayanaamsha.get_offset(2458434.083333251) == 24.094859396693067


def disabled_test_swe_ayanaamsha_api():
  import swisseph as swe
  swe.set_sid_mode(swe.SIDM_LAHIRI)
  # city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  # jd = city.local_time_to_julian_day(year=2018, month=11, day=11, hours=6, minutes=0, seconds=0)
  assert swe.get_ayanamsa_ut(2458434.083333251) == 24.120535828308334


def test_get_angam():
  nd = NakshatraDivision(2444961.7125, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  assert nd.get_anga(AngaType.NAKSHATRA) == 16
  assert nd.get_anga(AngaType.TITHI) == 28
  assert nd.get_anga(AngaType.YOGA) == 8
  assert nd.get_anga(AngaType.KARANA) == 55
  assert nd.get_solar_raashi() == 9


def test_get_anga_span_solar_month():
  from jyotisha.panchaanga.temporal import time
  span_finder = AngaSpanFinder(anga_type=AngaType.SOLAR_MONTH, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)

  assert span_finder.find(jd1=2458222.0333434483-32, jd2=2458222.0333434483 + 4, target_anga_id=12,).to_tuple() == (2458192.24785228, 2458222.6026552585)

  jd2 = time.utc_gregorian_to_jd(time.Date(2020, 4, 16))
  assert span_finder.find(jd1=jd2-32, jd2=jd2, target_anga_id=1).to_tuple() == (2458953.1096598045, None)

  assert span_finder.find(jd1=2458133.0189002366-32, jd2=2458133.0189002366, target_anga_id=10,).to_tuple() == (2458132.8291680976, None)


def test_get_anga_span_tithi():
  span_finder = AngaSpanFinder(anga_type=AngaType.TITHI, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)

  assert span_finder.find(jd1=2458102.5, jd2=2458108.5, target_anga_id=30).to_tuple() == (2458104.6663699686, 2458105.771125107)
  
  assert span_finder.find(jd1=2444959.54042, jd2=2444963.54076, target_anga_id=27).to_tuple() == (2444960.4924699212, 2444961.599213224)


def test_get_new_moons_in_period():
  new_moon_jds = zodiac.get_tithis_in_period(jd_start=time.utc_gregorian_to_jd(Date(year=2020, month=1, day=1)), jd_end=time.utc_gregorian_to_jd(Date(year=2020, month=6, day=30)))
  assert new_moon_jds == [2458872.36655025,
                          2458902.0647052005,
                          2458931.792117506,
                          2458961.5055956016,
                          2458991.1712410315,
                          2459020.765607745]