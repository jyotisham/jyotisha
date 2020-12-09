import argparse
from urllib.request import urlopen

import telegram

from jyotisha.panchaanga import spatio_temporal


def send_panchaanga(channel_id, token, md_url_base, html_url_base):
  bot = telegram.Bot(token=token)
  shaka_year = ""
  bengaLUru = spatio_temporal.City.get_city_from_db("sahakAra nagar, bengaLUru")
  today = bengaLUru.get_timezone_obj().current_time()
  day_path = "%04d-%02d/%04d-%02d-%02d" % (today.year, today.month, today.year, today.month, today.day)
  md_url = "%s/%s.md" % (md_url_base, day_path)
  html_url = "%s/%s/" % (html_url_base, day_path)
  md = "%s\n\n%s" % (html_url, urlopen(md_url).read().decode("utf-8"))
  bot.sendMessage(chat_id="-" + channel_id, text=md)
