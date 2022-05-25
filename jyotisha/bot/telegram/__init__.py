import logging
from datetime import datetime, timedelta
from urllib.request import urlopen

import regex
import telegram

from jyotisha.panchaanga.temporal import era
from jyotisha.panchaanga.writer.generation_project import get_canonical_path


def send_panchaanga(city, channel_id, token, computation_system_str, md_url_base, html_url_base, date_str=None, next_day=False, dry_run=False):
  bot = telegram.Bot(token=token)
  if date_str is None:
    today = city.get_timezone_obj().current_time()
    date_str = "%04d-%02d-%02d" % (today.year, today.month, today.day)
  if next_day:
    tomorrow = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)
    date_str = "%04d-%02d-%02d" % (tomorrow.year, tomorrow.month, tomorrow.day)
  import urllib
  city_url_segment = urllib.parse.quote(city.name)
  out_path_md = get_canonical_path(city=city_url_segment, computation_system_str=computation_system_str, year=today.year, year_type=era.ERA_GREGORIAN, output_dir=md_url_base)

  md_url = "%s_monthly/%s/%s.md" % (out_path_md, date_str[:7], date_str)

  city_url_segment = regex.sub("[^a-zA-Z]+", "-", city.name)
  out_path_html = get_canonical_path(city=city_url_segment, computation_system_str=computation_system_str, year=today.year, year_type=era.ERA_GREGORIAN, output_dir=html_url_base)
  html_url = "%s_monthly/%04d-%02d/%04d-%02d-%02d" % (out_path_html, today.year, today.month, today.year, today.month, today.day)
  logging.info("md_url: %s" % md_url)
  logging.info("html_url: %s" % html_url)
  md = "%s\n\n%s" % (html_url, urlopen(md_url).read().decode("utf-8"))
  if len(md) >= telegram.MAX_MESSAGE_LENGTH - 100:
    md = md[:telegram.MAX_MESSAGE_LENGTH - 500] + "\n\n Message truncated. Please visit URL at top for full details."
  logging.info("Sending message: \n%s", md)
  if not dry_run:
    # md = "## माघः-11-23,कन्या-हस्तः🌛🌌◢◣धनुः-पूर्वाषाढा-09-22🌌🌞◢◣सहस्यः-10-17🪐🌞 बुधः"
    bot.sendMessage(chat_id="-" + channel_id, text=md)
