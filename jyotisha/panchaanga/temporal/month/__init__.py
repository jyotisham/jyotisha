import sys

from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.zodiac import AngaSpan, NakshatraDivision
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class LunarMonthAssigner(JsonObject):
  MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA = "MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA"
  SOLSTICE_POST_DARK_10_ASHIKA = "SOLSTICE_POST_DARK_10_ASHIKA"
  
  def __init__(self, ayanaamsha_id):
    self.ayanaamsha_id = ayanaamsha_id

  def get_month_sunrise(self, daily_panchaanga):
    pass

  @classmethod
  def get_assigner(cls, computation_system):
    if computation_system.lunar_month_assigner_type == LunarMonthAssigner.MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA:
      return MultiNewmoonSolarMonthAdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    elif computation_system.lunar_month_assigner_type == LunarMonthAssigner.SOLSTICE_POST_DARK_10_ASHIKA:
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
    last_new_moon = AngaSpan.find(
      daily_panchaanga.jd_sunrise - daily_panchaanga.sunrise_day_angas.tithi_at_sunrise - 3, daily_panchaanga.jd_sunrise - daily_panchaanga.sunrise_day_angas.tithi_at_sunrise + 3,
      zodiac.AngaType.TITHI, 30, ayanaamsha_id=self.ayanaamsha_id)
    this_new_moon = AngaSpan.find(
      last_new_moon.jd_start + 24, last_new_moon.jd_start + 32,
      zodiac.AngaType.TITHI, 30, ayanaamsha_id=self.ayanaamsha_id)
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

  def get_month_sunrise(self, daily_panchaanga):
    """ Assigns Lunar months to days in the period
    
    Implementation note: Works by looking at solar months and new moons (which makes it easy to deduce adhika-mAsa-s.)
    
    :return: 
    """
    # tithi_at_sunrise gives a rough indication of the number of days since last new moon. We now find a more precise interval below.
    pass

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
