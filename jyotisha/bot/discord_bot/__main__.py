import argparse

from jyotisha.bot.discord_bot import send_panchaanga
from jyotisha.panchaanga import spatio_temporal

# Example arguments:
# --token "????" --city "sahakAra nagar, bengaLUru" --channel_id 1019147573505839156 --md_url_base "https://raw.githubusercontent.com/jyotisham/jyotisha/generated-output/" --html_url_base "https://jyotisham.github.io/jyotisha/output/" --computation_system_str SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_AT_180 --next_day --dry_run

parser = argparse.ArgumentParser(description='Telgram bot.')
parser.add_argument('--city', type=str, default="sahakAra nagar, bengaLUru", nargs='?')
parser.add_argument('--channel_id', type=str, nargs='?')
parser.add_argument('--token', type=str, nargs='?')
parser.add_argument('--computation_system_str', type=str, nargs='?')
parser.add_argument('--md_url_base', type=str, nargs='?')
parser.add_argument('--html_url_base', type=str, nargs='?')
parser.add_argument('--date', type=str, default=None, nargs='?')
parser.add_argument('--next_day', action=argparse.BooleanOptionalAction, default=False)
parser.add_argument('--dry_run', action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

city = spatio_temporal.City.get_city_from_db(args.city)

send_panchaanga(city=city, channel_id=args.channel_id, token=args.token, md_url_base=args.md_url_base, computation_system_str=args.computation_system_str, html_url_base=args.html_url_base, date_str=args.date, next_day=args.next_day, dry_run=args.dry_run)