"""
Module where we generate and present certain calendars automatically for handy use and as usage examples.
"""
import codecs
import os
import shutil

import toml
from doc_curation.md_helper import MdFile

import jyotisha
from indic_transliteration import xsanscript
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.writer import ics, md
from jyotisha.panchaanga.writer.md import get_computation_parameters_md
from jyotisha.panchaanga.writer.table.day_details import to_table_dict

output_dir = os.path.join(os.path.dirname(os.path.dirname(jyotisha.__file__)), "hugo-source", "content", "output")


def dump_ics_md_pair(panchaanga, period_str):
  ics_calendar = ics.compute_calendar(panchaanga)
  output_file_ics = os.path.join(output_dir, panchaanga.city.name, str(panchaanga.computation_system), '%s.ics' % period_str)
  ics.write_to_file(ics_calendar, output_file_ics)

  md_file = MdFile(file_path=output_file_ics.replace(".ics", ".md"), frontmatter_type=MdFile.YAML)
  intro = "## 00 Intro\n### Related files\n- [ics](../%s)\n" % str(os.path.basename(output_file_ics))
  md_content = "%s\n%s" % (intro, md.make_md(panchaanga=panchaanga))
  md_file.dump_to_file(metadata={"title": period_str.split("/")[-1]}, md=md_content, dry_run=False)

  monthly_file_path = md_file.file_path.replace(".md", "_monthly.md")
  monthly_dir = monthly_file_path.replace(".md", "/")
  shutil.rmtree(path=monthly_dir, ignore_errors=True)
  shutil.copy(md_file.file_path, monthly_file_path)
  monthly_md_file = MdFile(file_path=monthly_file_path)
  monthly_md_file.set_title_from_filename(dry_run=False, transliteration_target=None)
  monthly_md_file.split_to_bits(source_script=None, dry_run=False, indexed_title_pattern=None)
  MdFile.apply_function(fn=MdFile.split_to_bits, dir_path=monthly_dir, frontmatter_type=MdFile.TOML, source_script=None, dry_run=False, indexed_title_pattern=None)


def dump_common(year, city, year_type):
  computation_system = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180
  panchaanga = annual.get_panchaanga_for_year(city=city, year=year, computation_system=computation_system, year_type=year_type, allow_precomputed=False)
  dump_ics_md_pair(panchaanga=panchaanga, period_str="%s/%04d" % (year_type, year))


def dump_kauNDinyAyana(year, city, year_type):
  computation_system = ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180
  computation_system.festival_options.repos = [RulesRepo(name="gRhya/general")]
  computation_system.festival_options.aparaahna_as_second_half = True
  computation_system.festival_options.prefer_eight_fold_day_division = True
  panchaanga = annual.get_panchaanga_for_year(city=city, year=year, computation_system=computation_system, year_type=year_type, allow_precomputed=False)
  dump_ics_md_pair(panchaanga=panchaanga, period_str="%s/%04d" % (year_type, year))


def dump_history(year, city, script=xsanscript.DEVANAGARI):
  year_type = RulesRepo.ERA_GREGORIAN
  computation_system = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180
  panchaanga = annual.get_panchaanga_for_year(city=city, year=year, computation_system=computation_system, year_type=year_type, allow_precomputed=False)
  year_table = to_table_dict(panchaanga=panchaanga )
  out_path = os.path.join(output_dir, panchaanga.city.name, str(panchaanga.computation_system), year_type, '%s00s/%s0s/%s.toml' % (str(year)[:2], str(year)[:3], str(year)))
  os.makedirs(os.path.dirname(out_path), exist_ok=True)
  with codecs.open(out_path, "w") as fp:
    toml.dump(year_table, fp)
  MdFile.fix_index_files(dir_path=output_dir, transliteration_target=None, dry_run=False)

  computation_params = get_computation_parameters_md(panchaanga=panchaanga, scripts=[script])
  out_path_md = out_path.replace(".toml", "_summary.md")
  md = """##Intro\n%s\n\n## Table
  <div class="spreadsheet" src="../%s.toml" fullHeightWithRowsPerScreen=8> </div>""" % (computation_params, 
    str(year))
  md_file = MdFile(file_path=out_path_md)
  md_file.dump_to_file(metadata={"title": str(year)}, md=md, dry_run=False)
