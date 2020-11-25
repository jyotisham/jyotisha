import os

from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.writer import ics


def dump_ics(year=1942):
  output_dir = os.path.join(os.path.dirname(__file__), "output")
  city = spatio_temporal.City.get_city_from_db("bengaLUru-snagar")
  computation_system = ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180
  # computation_system.options.fest_repos = "gRhya/general"
  tropical_panchaanga = annual.get_panchaanga_for_shaka_year(city=city, year=year, computation_system=computation_system)
  ics_calendar = ics.compute_calendar(tropical_panchaanga)
  output_file = os.path.expanduser('%s/%s_shaka-%d.ics' % (str(output_dir), city.name, year))
  ics.write_to_file(ics_calendar, output_file)
  


if __name__ == '__main__':
    dump_ics()