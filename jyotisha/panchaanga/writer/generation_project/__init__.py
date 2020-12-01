"""
Module where we generate and present certain calendars automatically for handy use and as usage examples.
"""

import os

from doc_curation.md_helper import MdFile

import jyotisha
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.writer import ics, md

output_dir = os.path.join(os.path.dirname(os.path.dirname(jyotisha.__file__)), "hugo-source", "content", "output")


def dump_ics_md_pair(panchaanga, period_str):
  ics_calendar = ics.compute_calendar(panchaanga)
  output_file_ics = os.path.join(output_dir, panchaanga.city.name, str(panchaanga.computation_system), "shaka_year", '%s.ics' % period_str)
  ics.write_to_file(ics_calendar, output_file_ics)

  md_file = MdFile(file_path=output_file_ics.replace(".ics", ".md"), frontmatter_type=MdFile.YAML)
  ics_link = "## Related files\n- [ics](%s)\n" % str(output_file_ics)
  md_content = "%s\n%s" % (ics_link, md.make_md(panchaanga=panchaanga))
  md_file.dump_to_file(metadata={"title": str(panchaanga.start_date.year)}, md=md_content, dry_run=False)


def dump_common(year, city):
  computation_system = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180
  panchaanga = annual.get_panchaanga_for_shaka_year(city=city, year=year, computation_system=computation_system)
  dump_ics_md_pair(panchaanga=panchaanga, period_str=str(year))


def dump_kauNDinyAyana(year, city):
  computation_system = ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180
  computation_system.options.fest_repos = [RulesRepo(name="gRhya/general")]
  tropical_panchaanga = annual.get_panchaanga_for_shaka_year(city=city, year=year, computation_system=computation_system, allow_precomputed=False)
  dump_ics_md_pair(panchaanga=tropical_panchaanga, period_str=str(year))
  

