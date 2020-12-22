import sys

from jyotisha.panchaanga.temporal import zodiac, tithi
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, AngaSpanFinder, Ayanamsha
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class LunarMonthAssigner(JsonObject):
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA = "MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA"
  MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA = "MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA"
  SOLSTICE_POST_DARK_10_ADHIKA = "SOLSTICE_POST_DARK_10_ADHIKA"
  
  def __init__(self, ayanaamsha_id):
    super().__init__()
    self.ayanaamsha_id = ayanaamsha_id

  def get_month_sunrise(self, daily_panchaanga):
    pass

  @classmethod
  def get_assigner(cls, computation_system):
    if computation_system.lunar_month_assigner_type == LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA:
      return MultiNewmoonSolarMonthAdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    elif computation_system.lunar_month_assigner_type == LunarMonthAssigner.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA:
      return MultiFullmoonSolarMonthAdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    elif computation_system.lunar_month_assigner_type == LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA:
      return SolsticePostDark10AdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    else:
      raise ValueError("Invalid assigner_id " + computation_system.lunar_month_assigner_type)


class MultiLunarPhaseSolarMonthAdhikaAssigner(LunarMonthAssigner):
  """Let us consider a lunar month defined as ending with a particular lunar tithi. This assigner marks a month as adhika iff that month does not have a solar sankrAnti."""

  def __init__(self, ayanaamsha_id, month_end_tithi):
    super(MultiLunarPhaseSolarMonthAdhikaAssigner, self).__init__(ayanaamsha_id=ayanaamsha_id)
    self.month_end_tithi = month_end_tithi

  """
  
  प्रचलितायाम् अर्वाचीनायां पद्धतौ अर्वाचीनस्य राशिविभाजने आधृतस्य सौरमासस्य सङ्क्रान्तिं स्वीकृत्य “असङ्क्रान्ति-मासो ऽधिमास” इति परिभाषया अधिकमासगणना क्रियते ।
  """
  def get_month_sunrise(self, daily_panchaanga):
    """ Assigns Lunar months to days in the period
    
    Implementation note: Works by looking at solar months and month-end tithis (which makes it easy to deduce adhika-mAsa-s.)
    
    :return: 
    """
    # tithi_at_sunrise gives a rough indication of the number of days since last new moon. We now find a more precise interval below.
    anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=zodiac.AngaType.TITHI)

    if self.month_end_tithi < daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index:
      approx_days_since_last_end_tithi =  daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index - self.month_end_tithi
    else:
      approx_days_since_last_end_tithi = daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index + (30 - self.month_end_tithi)

    last_lunar_phase = anga_finder.find(
      jd1=daily_panchaanga.jd_sunrise - approx_days_since_last_end_tithi - 3, jd2=daily_panchaanga.jd_sunrise - approx_days_since_last_end_tithi + 3, target_anga_id=self.month_end_tithi)
    this_new_moon = anga_finder.find(
      jd1=last_lunar_phase.jd_start + 24, jd2=last_lunar_phase.jd_start + 32,
      target_anga_id=self.month_end_tithi)
    last_new_moon_solar_raashi = NakshatraDivision(last_lunar_phase.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    this_new_moon_solar_raashi = NakshatraDivision(this_new_moon.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    is_adhika = last_new_moon_solar_raashi == this_new_moon_solar_raashi

    if is_adhika:
      return this_new_moon_solar_raashi + .5
    else:
      return this_new_moon_solar_raashi


class MultiNewmoonSolarMonthAdhikaAssigner(MultiLunarPhaseSolarMonthAdhikaAssigner):
  def __init__(self, ayanaamsha_id):
    super(MultiNewmoonSolarMonthAdhikaAssigner, self).__init__(ayanaamsha_id=ayanaamsha_id, month_end_tithi=30)


class MultiFullmoonSolarMonthAdhikaAssigner(MultiLunarPhaseSolarMonthAdhikaAssigner):
  def __init__(self, ayanaamsha_id):
    super(MultiFullmoonSolarMonthAdhikaAssigner, self).__init__(ayanaamsha_id=ayanaamsha_id, month_end_tithi=15)


class SolsticePostDark10AdhikaAssigner(LunarMonthAssigner):
  """
  
  द्व्यूनं द्वि-षष्टि-भागेन दिनं सौराच् च पार्वणम् । यत्कृताव् उपजायेते मध्येऽन्ते चाऽधिमासकौ ।। इति वेदाङ्गज्योतिषे।
  केषुचिद् एव युगेषु, यथापेक्षम् अधिमासयोजनं स्यात्। किन्तु यदायदाऽधिकमासो योज्यते तदातदाऽयनान्ते एव शुचौ मासे (आषाढे) वा सहस्ये मासे (पौषे) वा द्वितीयशुचिमासरूपेण (द्वितीयाषाढरूपेण) वा द्वितीयसहस्यमासरूपेण (द्वितीयपौषरूपेण) वैवाऽधिकमासो योज्यते।
  
  एतादृशी व्यवस्था च - यदा दृक्-सिद्धसौरायनारम्भदिने (दक्षिणायनस्य वोत्तरायणस्य वापि) कृष्णपक्षस्य दशमी, ततः परा वा तिथिर् भवति तदैव तेन कृष्णपक्षेण युक्तोऽमावास्यान्तो मासोऽधिको मास इति स्वीक्रियते, -यदा तु दृक्सिद्धसौरायनारम्भदिने कृष्णपक्षस्य नवमी वा ततः पूर्वा वा तिथिर् भवति तदा तु तेन कृष्णपक्षेण युक्तोऽमावास्यान्तो मासोऽधिको मास इति न स्वीक्रियते।
  
  वेदाङ्गज्योतिषानुरूपाया गणनाया प्रयोगः काष्ठमण्डपनगरे मल्लानां शासनकालपर्यन्तमासीदिति शिलालेखेभ्य एव ज्ञायते।
  """

  @classmethod
  def _is_tithi_post_dark10(cls, jd):
    if tithi.get_tithi(jd=jd).index > 15 + 9:
      return True
    else:
      return False

  @classmethod
  def _month_from_previous_jd_month_provisional(cls, jd, prev_jd, prev_jd_month):
    """Deduce (provisional) month from a previous known day's month."""
    span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.TITHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
    tithi_1_jds = span_finder.get_spans_in_period(jd_start=prev_jd, jd_end=jd, target_anga_id=1)
    is_prev_month_adhika = str(prev_jd_month.index).endswith(".5")
    if is_prev_month_adhika:
      lunar_month = prev_jd_month + max(0, len(tithi_1_jds) - 0.5)
    else:
      lunar_month = prev_jd_month + len(tithi_1_jds)
    return lunar_month

  @classmethod
  def _get_solstice_lunar_month(cls, solstice_tropical_month_span):
    """Get exact month for the solstice_tropical_month_span.jd_start.
    
    """
    prev_solstice_tropical_month_span = zodiac.get_previous_solstice_month_span(jd=solstice_tropical_month_span.jd_start - 1)
    if not cls._is_tithi_post_dark10(jd=solstice_tropical_month_span.jd_start):
      if not cls._is_tithi_post_dark10(jd=prev_solstice_tropical_month_span.jd_start):
        return solstice_tropical_month_span.anga
      else:
        prev_solstice_lunar_month = cls._get_solstice_lunar_month(solstice_tropical_month_span=prev_solstice_tropical_month_span)
        lunar_month = cls._month_from_previous_jd_month_provisional(jd=solstice_tropical_month_span.jd_start, prev_jd=prev_solstice_tropical_month_span.jd_start, prev_jd_month=prev_solstice_lunar_month)
        return lunar_month
    else:
      # Was there an adhika maasa in the recent past?
      # If so, this month will not be one, even if post-dark10 solsticial. 
      if not cls._is_tithi_post_dark10(jd=prev_solstice_tropical_month_span.jd_start):
        return solstice_tropical_month_span.anga + 0.5
      else:
        prev_solstice_lunar_month = cls._get_solstice_lunar_month(solstice_tropical_month_span=prev_solstice_tropical_month_span)
        lunar_month = cls._month_from_previous_jd_month_provisional(jd=solstice_tropical_month_span.jd_start, prev_jd=prev_solstice_tropical_month_span.jd_start, prev_jd_month=prev_solstice_lunar_month)
        return lunar_month

  def get_month_sunrise(self, daily_panchaanga):
    """ Assigns Lunar months to days in the period
        
    :return: 
    """
    solstice_tropical_month_span = zodiac.get_previous_solstice_month_span(jd=daily_panchaanga.jd_sunrise)
    solstice_lunar_month = SolsticePostDark10AdhikaAssigner._get_solstice_lunar_month(solstice_tropical_month_span=solstice_tropical_month_span)
    is_solstice_lunar_month_adhika = str(solstice_lunar_month.index).endswith(".5")
    if is_solstice_lunar_month_adhika:
      lunar_month = self._month_from_previous_jd_month_provisional(jd=daily_panchaanga.jd_sunrise, prev_jd=solstice_tropical_month_span.jd_start, prev_jd_month=solstice_lunar_month)
      return lunar_month
    else:
      # At this point, we're sure that there was no previous postDark10 solstice.
      # Are we in a lunar month containing solstice?
      tropical_month = zodiac.get_tropical_month(jd=daily_panchaanga.jd_sunrise)
      if tropical_month.index in [3, 9]:
        anga_span_finder = AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=AngaType.TROPICAL_MONTH)
        next_solstice_tropical_month_span = anga_span_finder.find(jd1=daily_panchaanga.jd_sunrise, jd2=daily_panchaanga.jd_sunrise + 32, target_anga_id=tropical_month + 1)
        span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.TITHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
        tithi_1_jds = span_finder.get_spans_in_period(jd_start=daily_panchaanga.jd_sunrise, jd_end=next_solstice_tropical_month_span.jd_start, target_anga_id=1)
        if len(tithi_1_jds) == 0:
          solstice_lunar_month = SolsticePostDark10AdhikaAssigner._get_solstice_lunar_month(solstice_tropical_month_span=next_solstice_tropical_month_span)
          return solstice_lunar_month

      # The default case.
      lunar_month = self._month_from_previous_jd_month_provisional(jd=daily_panchaanga.jd_sunrise, prev_jd=solstice_tropical_month_span.jd_start, prev_jd_month=solstice_lunar_month)
      return lunar_month







# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
