import logging
from urllib.request import urlopen

import telegram

from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.writer.generation_project import get_canonical_path


def send_panchaanga(channel_id, token, computation_system_str, md_url_base, html_url_base):
  bot = telegram.Bot(token=token)
  bengaLUru = spatio_temporal.City.get_city_from_db("sahakAra nagar, bengaLUru")
  today = bengaLUru.get_timezone_obj().current_time()
  out_path_md = get_canonical_path(city="", computation_system_str=computation_system_str, year=today.year, year_type=RulesRepo.ERA_GREGORIAN, output_dir=md_url_base)
  
  day_path = "%s/%04d_monthly/%04d-%02d/%04d-%02d-%02d" % (out_path_md, today.year, today.year, today.month, today.year, today.month, today.day)
  md_url = "%s/%s.md" % (md_url_base, day_path)

  out_path_html = get_canonical_path(city="", computation_system_str=computation_system_str, year=today.year, year_type=RulesRepo.ERA_GREGORIAN, output_dir=html_url_base)
  html_url = "%s/%s/" % (out_path_html, day_path)
  logging.info("md_url: %s" % md_url)
  logging.info("html_url: %s" % html_url)
  md = "%s\n\n%s" % (html_url, urlopen(md_url).read().decode("utf-8"))
  if len(md) >= telegram.MAX_MESSAGE_LENGTH - 100:
    md = md[:telegram.MAX_MESSAGE_LENGTH - 500] + "\n\n Message truncated. Please visit URL at top for full details."
  bot.sendMessage(chat_id="-" + channel_id, text=md)
