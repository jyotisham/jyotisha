'''
Key Features
------------

#. Generate an A3 PDF of a *monthly calendar* using Python / TeX (using
   ``gen_monthly_cal.sh`` or ``write_monthly_panchaanga_tex.py``)
#. Generate an A5 PDF of a *daily calendar* using Python / TeX (using
   ``gen_daily_cal.sh`` or ``write_daily_panchaanga_tex.py``)
#. Generate an ICS calendar file for using with calendaring applications
   (using ``gen_ics.sh`` or ``ics.py``)

The PDFs and ICS are best generated using a Devanagari (and Tamil)
scripts, though ISO works as well (mostly).

Dependencies
~~~~~~~~~~~~

-  Both Python 3 and LaTeX are necessary to generate the panchaanga
   PDFs; to generate the ICS alone, only Python 3 suffices
-  Python: pyswisseph, SciPy, icalendar and pytz
-  XeLaTeX / fontspec and a few other ‘regular’ packages
-  Fonts: Sanskrit 2003, Noto Sans UI, Noto Sans Devanagari, Noto Sans Tamil

Usage
-----

Helper scripts and Downloadable Panchangas (PDF/ICS)
~~~~~~~~~~~~~~
See https://github.com/karthikraman/panchaanga repository.

'''


import logging

from indic_transliteration import sanscript
from jyotisha.panchaanga.temporal.names import translate_or_transliterate

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def transliterate_and_print(text, script, output_stream):
  print(translate_or_transliterate(text=text, script=script, source_script=sanscript.DEVANAGARI), file=output_stream)  
