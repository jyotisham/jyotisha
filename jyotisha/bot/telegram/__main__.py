import argparse

from jyotisha.bot.telegram import send_panchaanga
from jyotisha.panchaanga import spatio_temporal

parser = argparse.ArgumentParser(description='Telgram bot.')
parser.add_argument('--city', type=str, default="sahakAra nagar, bengaLUru", nargs='?')
parser.add_argument('--channel_id', type=str, nargs='?')
parser.add_argument('--token', type=str, nargs='?')
parser.add_argument('--computation_system_str', type=str, nargs='?')
parser.add_argument('--md_url_base', type=str, nargs='?')
parser.add_argument('--html_url_base', type=str, nargs='?')
args = parser.parse_args()

city = spatio_temporal.City.get_city_from_db(args.city)

send_panchaanga(city=city, channel_id=args.channel_id, token=args.token, md_url_base=args.md_url_base, computation_system_str=args.computation_system_str, html_url_base=args.html_url_base)