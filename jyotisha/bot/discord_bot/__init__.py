import logging
import sys

import discord
from jyotisha.bot import get_panchaanga_md




class SingleMessageSender(discord.Client):
  intents = discord.Intents.default()
  intents.message_content = True
  

  def __init__(self, message, channel_id):
    super(SingleMessageSender, self).__init__(intents=SingleMessageSender.intents)
    self.message = message
    self.channel_id = channel_id
    

  async def on_ready(self):
    logging.info('Logged on as {self.user}')
    channel = self.get_channel(int(self.channel_id))
    await channel.send(self.message)
    logging.info("Sent message.")
    sys.exit()



def send_panchaanga(city, channel_id, token, computation_system_str, md_url_base, html_url_base, date_str=None, next_day=False, dry_run=False):
  md = get_panchaanga_md(city, computation_system_str, date_str, html_url_base, md_url_base, next_day)
  if not dry_run:
    # md = "## माघः-11-23,कन्या-हस्तः🌛🌌◢◣धनुः-पूर्वाषाढा-09-22🌌🌞◢◣सहस्यः-10-17🪐🌞 बुधः"
    client = SingleMessageSender(message=md, channel_id=channel_id)
    client.run(token)

