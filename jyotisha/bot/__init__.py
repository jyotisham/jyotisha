import logging
from datetime import datetime, timedelta
from urllib.request import urlopen

import regex

from jyotisha.panchaanga.temporal import era
from jyotisha.panchaanga.writer.generation_project import get_canonical_path


def get_panchaanga_md(city, computation_system_str, date_str, html_url_base, md_url_base, next_day, max_length):
  if date_str is None:
    today = city.get_timezone_obj().current_time()
    date_str = "%04d-%02d-%02d" % (today.year, today.month, today.day)
    year = int(today.year)
  else:
    year = int(date_str[:4])
  if next_day:
    tomorrow = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)
    date_str = "%04d-%02d-%02d" % (tomorrow.year, tomorrow.month, tomorrow.day)
    year = int(tomorrow.year)
  import urllib
  city_url_segment = urllib.parse.quote(city.name)
  out_path_md = get_canonical_path(city=city_url_segment, computation_system_str=computation_system_str, year=year,
                                   year_type=era.ERA_GREGORIAN, output_dir=md_url_base)
  md_url = "%s_monthly/%s/%s.md" % (out_path_md, date_str[:7], date_str)
  city_url_segment = regex.sub("[^a-zA-Z]+", "-", city.name)
  out_path_html = get_canonical_path(city=city_url_segment, computation_system_str=computation_system_str, year=year,
                                     year_type=era.ERA_GREGORIAN, output_dir=html_url_base)
  html_url = "%s_monthly/%s/%s" % (out_path_html, date_str[:7], date_str)
  logging.info("md_url: %s" % md_url)
  logging.info("html_url: %s" % html_url)
  md = "%s\n\n%s" % (html_url, urlopen(md_url).read().decode("utf-8"))
  if len(md) >= max_length - 100:
    md = md[:max_length - 500] + "\n\n Message truncated. Please visit URL at top for full details."
  logging.info("Sending message: \n%s", md)
  return md
