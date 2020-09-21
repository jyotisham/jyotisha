'''
Key Features
------------

#. Generate an A3 PDF of a *monthly calendar* using Python / TeX (using
   ``gen_monthly_cal.sh`` or ``write_monthly_panchangam_tex.py``)
#. Generate an A5 PDF of a *daily calendar* using Python / TeX (using
   ``gen_daily_cal.sh`` or ``write_daily_panchangam_tex.py``)
#. Generate an ICS calendar file for using with calendaring applications
   (using ``gen_ics.sh`` or ``ics.py``)

The PDFs and ICS are best generated using a Devanagari (and Tamil)
scripts, though IAST works as well (mostly).

Dependencies
~~~~~~~~~~~~

-  Both Python 3 and LaTeX are necessary to generate the panchangam
   PDFs; to generate the ICS alone, only Python 3 suffices
-  Python: pyswisseph, SciPy, icalendar and pytz
-  XeLaTeX / fontspec and a few other ‘regular’ packages
-  Fonts: Sanskrit 2003, Noto Sans UI, Noto Sans Devanagari, Noto Sans Tamil

Usage
-----

Helper scripts and Downloadable Panchangams (PDF/ICS)
~~~~~~~~~~~~~~
See https://github.com/karthikraman/panchangam repository.

'''


import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)
