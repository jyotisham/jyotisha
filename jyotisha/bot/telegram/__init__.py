import telegram

from jyotisha.bot import get_panchaanga_md


def send_panchaanga(city, channel_id, token, computation_system_str, md_url_base, html_url_base, date_str=None, next_day=False, dry_run=False):
  bot = telegram.Bot(token=token)
  md = get_panchaanga_md(city, computation_system_str, date_str, html_url_base, md_url_base, next_day, max_length=telegram.MAX_MESSAGE_LENGTH)
  if not dry_run:
    # md = "## माघः-11-23,कन्या-हस्तः🌛🌌◢◣धनुः-पूर्वाषाढा-09-22🌌🌞◢◣सहस्यः-10-17🪐🌞 बुधः"
    bot.sendMessage(chat_id="-" + channel_id, text=md)


