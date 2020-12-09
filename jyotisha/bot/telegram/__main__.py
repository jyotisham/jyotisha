import argparse

from jyotisha.bot.telegram import send_panchaanga

parser = argparse.ArgumentParser(description='Telgram bot.')
parser.add_argument('--channel_id', type=str, nargs='?')
parser.add_argument('--token', type=str, nargs='?')
parser.add_argument('--md_url_base', type=str, nargs='?')
parser.add_argument('--html_url_base', type=str, nargs='?')
args = parser.parse_args()
send_panchaanga(channel_id=args.channel_id, token=args.token, md_url_base=args.md_url_base, html_url_base=args.html_url_base)