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
    await self.close()
    self.loop.stop()



def send_panchaanga(city, channel_id, token, computation_system_str, md_url_base, html_url_base, date_str=None, next_day=False, dry_run=False):
  md = get_panchaanga_md(city, computation_system_str, date_str, html_url_base, md_url_base, next_day, max_length=1950)
  
  # Getting mangled text like:
  # - 🌞-🪐 अमढगरह - गर (166.93° → 168.03°), मङगल (98.59° → 99.10°), शनशचर (-147.57° → -146.54°), शकर (9.96° → 9.70°), बध (-15.46° → -13.90°)
  # Reported a bug. Putting in code (```xyz```) format did not help.
  if not dry_run:
    # md = "## माघः-11-23,कन्या-हस्तः🌛🌌◢◣धनुः-पूर्वाषाढा-09-22🌌🌞◢◣सहस्यः-10-17🪐🌞 बुधः"
    client = SingleMessageSender(message=md, channel_id=channel_id)
    client.run(token)

