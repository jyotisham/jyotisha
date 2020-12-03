from io import StringIO

from indic_transliteration import sanscript
from jyotisha import custom_transliteration
from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal.names import translate_or_transliterate

from jyotisha.panchaanga.writer.md import day_details


def make_md(panchaanga, scripts=None, languages=None):
  if scripts is None:
    scripts = [sanscript.DEVANAGARI]
  if languages is None:
    languages = ["sa"]
  output_stream = StringIO()
  print('- 🌏**%s** (%s)  ' % (
    translate_or_transliterate('क्षेत्रम्', scripts[0], source_script=sanscript.DEVANAGARI), panchaanga.city.get_transliterated_name(script=scripts[0])),
        file=output_stream)
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for day_index, daily_panchaanga in enumerate(daily_panchaangas):
    if daily_panchaanga.date < panchaanga.start_date or daily_panchaanga.date > panchaanga.end_date:
      continue

    (title, details) = day_details.day_summary(d=day_index, panchaanga=panchaanga, script=scripts[0])
    print("## %s◢◣%s" % (daily_panchaanga.date.get_date_str(), title), file=output_stream)
    print(details, file=output_stream)
    
    festival_md = day_details.get_festivals_md(daily_panchaanga=daily_panchaanga, panchaanga=panchaanga, languages=languages, scripts=scripts)
    if festival_md != "":
      print("### %s\n%s" % (names.translate_or_transliterate(text="utsavAH", script=scripts[0]), festival_md), file=output_stream)
  return output_stream.getvalue()

