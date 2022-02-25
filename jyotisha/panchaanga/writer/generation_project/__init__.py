"""
Module where we generate and present certain calendars automatically for handy use and as usage examples.
"""
import codecs
import logging
import os
import shutil

import toml
from doc_curation.md import library
from doc_curation.md.file import MdFile
from doc_curation.md.library import metadata_helper

import jyotisha
from indic_transliteration import sanscript
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal import ComputationSystem, era
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.writer import ics, md
from jyotisha.panchaanga.writer.md import get_computation_parameters_md
from jyotisha.panchaanga.writer.table.day_details import to_table_dict

output_dir = os.path.join(os.path.dirname(os.path.dirname(jyotisha.__file__)), "hugo-source", "content", "output")


def dump_ics_md_pair(panchaanga, period_str):
  ics_calendar = ics.compute_calendar(panchaanga)
  (year_type, year) = period_str.split("/")
  year = int(year)
  out_path = get_canonical_path(city=panchaanga.city.name, computation_system_str=str(panchaanga.computation_system), year=year, year_type=year_type)
  output_file_ics = os.path.join(out_path + ".ics")
  ics.write_to_file(ics_calendar, output_file_ics)

  md_file = MdFile(file_path=output_file_ics.replace(".ics", ".md"), frontmatter_type=MdFile.YAML)
  intro = "## 00 Intro\n### Related files\n- [ics](../%s)\n" % str(os.path.basename(output_file_ics))
  md_content = "%s\n%s" % (intro, md.make_md(panchaanga=panchaanga))
  md_file.dump_to_file(metadata={"title": year}, content=md_content, dry_run=False)

  monthly_file_path = md_file.file_path.replace(".md", "_monthly.md")
  monthly_dir = monthly_file_path.replace(".md", "/")
  shutil.rmtree(path=monthly_dir, ignore_errors=True)
  logging.info("%s exists? %s", monthly_dir, os.path.exists(monthly_dir))
  logging.info("Copying to %s", monthly_file_path)
  shutil.copy(md_file.file_path, monthly_file_path)
  monthly_md_file = MdFile(file_path=monthly_file_path)
  metadata_helper.set_title_from_filename(md_file=monthly_md_file, dry_run=False, transliteration_target=None)
  monthly_md_file.split_to_bits(source_script=None, dry_run=False, title_index_pattern=None)
  library.apply_function(fn=MdFile.split_to_bits, dir_path=monthly_dir, frontmatter_type=MdFile.TOML, source_script=None, dry_run=False, title_index_pattern=None)
  logging.info("%s exists? %s", monthly_dir, os.path.exists(monthly_dir))

  library.fix_index_files(dir_path=output_dir, transliteration_target=None, dry_run=False)


def dump_detailed(year, city, year_type, computation_system=ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180, allow_precomputed=False):
  logging.info("Generating detailed panchaanga for %s year %d (%s), with computation system %s ", city.name, year, year_type, str(computation_system))
  panchaanga = annual.get_panchaanga_for_year(city=city, year=year, computation_system=computation_system, year_type=year_type, allow_precomputed=allow_precomputed)
  dump_ics_md_pair(panchaanga=panchaanga, period_str="%s/%04d" % (year_type, year))


def dump_summary(year, city, script=sanscript.DEVANAGARI, computation_system=ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180, allow_precomputed=False):
  year_type = era.ERA_GREGORIAN
  logging.info("Generating summary panchaanga for %s year %d (%s), with computation system %s ", city.name, year, year_type, str(computation_system))
  panchaanga = annual.get_panchaanga_for_year(city=city, year=year, computation_system=computation_system, year_type=year_type, allow_precomputed=allow_precomputed)
  year_table = to_table_dict(panchaanga=panchaanga )
  out_path = get_canonical_path(city=panchaanga.city.name, computation_system_str=str(panchaanga.computation_system), year=year, year_type=year_type)
  os.makedirs(os.path.dirname(out_path), exist_ok=True)
  with codecs.open(out_path + ".toml", "w") as fp:
    toml.dump(year_table, fp)
  library.fix_index_files(dir_path=output_dir, transliteration_target=None, dry_run=False)

  computation_params = get_computation_parameters_md(panchaanga=panchaanga, scripts=[script])
  out_path_md = out_path + "_summary.md"
  md = """## Intro\n%s\n\n## Table
  <div class="spreadsheet" src="../%s.toml" fullHeightWithRowsPerScreen=4> </div>""" % (computation_params, 
    str(year))
  md_file = MdFile(file_path=out_path_md)
  md_file.dump_to_file(metadata={"title": "%d Summary" % (year)}, content=md, dry_run=False)


def get_canonical_path(city, computation_system_str, year, year_type=era.ERA_GREGORIAN, output_dir=output_dir):
  out_path = os.path.join(output_dir, city, computation_system_str, year_type,
                          '%02d00s/%03d0s/%04d' % (int(year / 100), int(year / 10), year))
  return out_path
