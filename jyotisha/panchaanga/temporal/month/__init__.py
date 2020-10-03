import math
import sys

from jyotisha.panchaanga.temporal import zodiac, tithi
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, AngaSpanFinder, AngaType, Ayanamsha
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class LunarMonthAssigner(JsonObject):
  MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA = "MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA"
  SOLSTICE_POST_DARK_10_ADHIKA = "SOLSTICE_POST_DARK_10_ADHIKA"
  
  def __init__(self, ayanaamsha_id):
    self.ayanaamsha_id = ayanaamsha_id

  def get_month_sunrise(self, daily_panchaanga):
    pass

  @classmethod
  def get_assigner(cls, computation_system):
    if computation_system.lunar_month_assigner_type == LunarMonthAssigner.MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA:
      return MultiNewmoonSolarMonthAdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    elif computation_system.lunar_month_assigner_type == LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA:
      return SolsticePostDark10AdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    else:
      raise ValueError("Invalid assigner_id " + computation_system.lunar_month_assigner_type)


class MultiNewmoonSolarMonthAdhikaAssigner(LunarMonthAssigner):
  """
  
  प्रचलितायाम् अर्वाचीनायां पद्धतौ अर्वाचीनस्य राशिविभाजने आधृतस्य सौरमासस्य सङ्क्रान्तिं स्वीकृत्य “असङ्क्रान्ति-मासो ऽधिमास” इति परिभाषया अधिकमासगणना क्रियते ।
  """
  def get_month_sunrise(self, daily_panchaanga):
    """ Assigns Lunar months to days in the period
    
    Implementation note: Works by looking at solar months and new moons (which makes it easy to deduce adhika-mAsa-s.)
    
    :return: 
    """
    # tithi_at_sunrise gives a rough indication of the number of days since last new moon. We now find a more precise interval below.
    anga_finder = zodiac.AngaSpanFinder(ayanaamsha_id=self.ayanaamsha_id, anga_type=zodiac.AngaType.TITHI)

    last_new_moon = anga_finder.find(
      jd1=daily_panchaanga.jd_sunrise - daily_panchaanga.sunrise_day_angas.tithi_at_sunrise - 3, jd2=daily_panchaanga.jd_sunrise - daily_panchaanga.sunrise_day_angas.tithi_at_sunrise + 3, target_anga_id=30)
    this_new_moon = anga_finder.find(
      jd1=last_new_moon.jd_start + 24, jd2=last_new_moon.jd_start + 32,
      target_anga_id=30)
    last_new_moon_solar_raashi = NakshatraDivision(last_new_moon.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    this_new_moon_solar_raashi = NakshatraDivision(this_new_moon.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    is_adhika = last_new_moon_solar_raashi == this_new_moon_solar_raashi

    if is_adhika:
      return (this_new_moon_solar_raashi % 12) + .5
    else:
      return this_new_moon_solar_raashi


class SolsticePostDark10AdhikaAssigner(LunarMonthAssigner):
  """
  
  द्व्यूनं द्वि-षष्टि-भागेन दिनं सौराच् च पार्वणम् । यत्कृताव् उपजायेते मध्येऽन्ते चाऽधिमासकौ ।। इति वेदाङ्गज्योतिषे।
  केषुचिद् एव युगेषु, यथापेक्षम् अधिमासयोजनं स्यात्। किन्तु यदायदाऽधिकमासो योज्यते तदातदाऽयनान्ते एव शुचौ मासे (आषाढे) वा सहस्ये मासे (पौषे) वा द्वितीयशुचिमासरूपेण (द्वितीयाषाढरूपेण) वा द्वितीयसहस्यमासरूपेण (द्वितीयपौषरूपेण) वैवाऽधिकमासो योज्यते।
  एतादृशी व्यवस्था च - यदा दृक्-सिद्धसौरायनारम्भदिने (दक्षिणायनस्य वोत्तरायणस्य वापि) कृष्णपक्षस्य दशमी, ततः परा वा तिथिर् भवति तदैव तेन कृष्णपक्षेण युक्तोऽमावास्यान्तो मासोऽधिको मास इति स्वीक्रियते, -यदा तु दृक्सिद्धसौरायनारम्भदिने कृष्णपक्षस्य नवमी वा ततः पूर्वा वा तिथिर् भवति तदा तु तेन कृष्णपक्षेण युक्तोऽमावास्यान्तो मासोऽधिको मास इति न स्वीक्रियते।
  """

  @classmethod
  def get_solstice_lunar_month(cls, solstice_tropical_month_span):
    solstice_tithi = tithi.get_tithi(jd=solstice_tropical_month_span.jd_start)
    if solstice_tithi > 15 + 9:
      solstice_in_adhika_maasa = True
    else:
      solstice_in_adhika_maasa = False
    solstice_lunar_month = solstice_tropical_month_span.name if not solstice_in_adhika_maasa else solstice_tropical_month_span.name + 0.5
    return solstice_lunar_month
    

  def get_month_sunrise(self, daily_panchaanga):
    """ Assigns Lunar months to days in the period
    
    Implementation note: Works by looking at solar months and new moons (which makes it easy to deduce adhika-mAsa-s.)
    
    :return: 
    """
    # Are we in a lunar month containing solstice? If so, calculation is straightforward and should be handled first.
    if daily_panchaanga.tropical_date_sunset.month in [3, 9]:
      anga_span_finder = AngaSpanFinder(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=AngaType.SOLAR_MONTH)
      solstice_tropical_month_span = anga_span_finder.find(jd1=daily_panchaanga.jd_sunrise, jd2=daily_panchaanga.jd_sunrise + 32, target_anga_id=daily_panchaanga.tropical_date_sunset.month + 1)
      tithi_1_jds = zodiac.get_tithis_in_period(jd_start=daily_panchaanga.jd_sunrise, jd_end=solstice_tropical_month_span.jd_start, tithi=1)
      if len(tithi_1_jds) == 0:
        solstice_lunar_month = SolsticePostDark10AdhikaAssigner.get_solstice_lunar_month(solstice_tropical_month_span=solstice_tropical_month_span)
        return solstice_lunar_month

    # Was there an adhika maasa in the recent past?
    solstice_tropical_month_span = daily_panchaanga.get_previous_solstice()

    solstice_lunar_month = SolsticePostDark10AdhikaAssigner.get_solstice_lunar_month(solstice_tropical_month_span=solstice_tropical_month_span)
    solstice_in_adhika_maasa = str(solstice_lunar_month).endswith(".5")
    tithi_1_jds = zodiac.get_tithis_in_period(jd_start=solstice_tropical_month_span.jd_start, jd_end=daily_panchaanga.jd_sunrise, tithi=1)
    if solstice_in_adhika_maasa:
      lunar_month = solstice_lunar_month + max(0, len(tithi_1_jds) - 0.5)
    else:
      lunar_month = solstice_lunar_month + len(tithi_1_jds)
    return lunar_month


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
