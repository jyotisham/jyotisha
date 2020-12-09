import argparse
from urllib.request import urlopen

import telegram


def send_panchaanga(channel_id, token, md_url_base):
  bot = telegram.Bot(token=token)
  shaka_year = ""
  url = "%s" % (md_url_base)
  md = urlopen(url).read().decode("utf-8")
  bot.sendMessage(chat_id="-" + channel_id, text=md)
