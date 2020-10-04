from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.spatio_temporal import annual, City
from jyotisha.panchaanga.temporal import ComputationSystem


def emit_vvasuki_calendar(common_panchaanga, tropical_panchaanga):
    pass


if __name__ == '__main__':
    city = spatio_temporal.City.get_city_from_db("bengaLUru-snagar")
    common_panchaanga = annual.get_panchaanga_for_shaka_year(city=city, year=1942, computation_system=ComputationSystem.MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA__CHITRA_180)
    tropical_panchaanga = annual.get_panchaanga_for_shaka_year(city=city, year=1942, computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
    emit_vvasuki_calendar(common_panchaanga=common_panchaanga, tropical_panchaanga=tropical_panchaanga)
