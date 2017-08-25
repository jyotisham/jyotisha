"""
Panchangam
==========

This project computes a *Pañcāṅgam* for a given location and given year.
It uses planetary positions from the Swiss ephemeris to (somewhat
accurately) calculate important aspects of a day, particularly the five
*āṅgams*, viz. *tithi* (moon phase), *nakshatram* (asterism), *yogam*,
*karaṇam* and *vāram*, and also the occurrence of various Hindu
festivals, which are usually decided by elaborate rules dependent on the
(combinations of the) *āṅgams*.

Key Features
------------

#. Generate an A3 PDF of a *monthly calendar* using Python / TeX (using
   ``gen_monthly_cal.sh`` or ``write_monthly_panchangam_tex.py``)
#. Generate an A5 PDF of a *daily calendar* using Python / TeX (using
   ``gen_daily_cal.sh`` or ``write_daily_panchangam_tex.py``)
#. Generate an ICS calendar file for using with calendaring applications
   (using ``gen_ics.sh`` or ``write_panchangam_ics.py``)

The PDFs and ICS are best generated using a Devanagari (and Tamil)
scripts, though IAST works as well (mostly).

Dependencies
~~~~~~~~~~~~

-  Both Python 3 and LaTeX are necessary to generate the panchangam
   PDFs; to generate the ICS alone, only Python 3 suffices
-  Python: `pyswisseph`_, `SciPy`_, `icalendar`_ and `pytz`_
-  XeLaTeX / fontspec and a few other ‘regular’ packages
-  Fonts: Sanskrit 2003, Candara, Vijaya (for Tamil)

Usage
-----

Organisation
~~~~~~~~~~~~

There are helpful scripts in the ``bin`` folder, while the Python codes
are in the ``panchangam`` folder. Generated PDFs will go to the ``pdf``
folder and ``.ics`` files will go to the ``ics`` folder, from which they
can be imported into any calendaring application.

Examples
~~~~~~~~

::

    cd panchangam/bin
    ./gen_daily_cal.sh Chennai 13:05:24 80:16:12 'Asia/Calcutta' 2017 devanagari lagna
    ./gen_monthly_cal.sh Chennai 13:05:24 80:16:12 'Asia/Calcutta' 2017 devanagari
    ./gen_ics.sh Chennai 13:05:24 80:16:12 'Asia/Calcutta' 2017 devanagari

The above codes generate two PDF files
(``daily-cal-2017-Chennai-deva.pdf``, ``cal-2017-Chennai-deva.pdf``) and
an ICS file (``Chennai-2017-devanagari.ics``) in the ``pdf`` and ``ics``
folders respectively.

Downloadable Panchangams (PDF/ICS)
----------------------------------

+-----+-------------------+-----------------+---------------+
| Cit | Monthly Calendar  | Daily Calendar  | ICS Calendar  |
| y   |                   |                 |               |
+=====+===================+=================+===============+
| **C | `A3 PDF`_         | `Kindle         | [Devanagari]( |
| hen |                   | friendly PDF`_  | https://githu |
| nai |                   |                 | b.com/karthik |
| **  |                   |                 | raman/panchan |
| (13 |                   |                 | gam/raw/maste |
| °05 |                   |                 | r/ics/Chennai |
| ’24 |                   |                 | -2017-devanag |
| ’‘N |                   |                 | ar            |
| ,   |                   |                 |               |
| 80° |                   |                 |               |
| 16’ |                   |                 |               |
| 12’ |                   |                 |               |
| ’E) |                   |                 |               |
+-----+-------------------+-----------------+---------------+

.. _here: https://github.com/karthikraman/panchangam/archive/master.zip
.. _pyswisseph: https://github.com/astrorigin/pyswisseph
.. _SciPy: https://www.scipy.org/
.. _icalendar: https://pypi.python.org/pypi/icalendar
.. _pytz: https://pypi.python.org/pypi/pytz
.. _A3 PDF: https://github.com/karthikraman/panchangam/raw/master/pdf/cal-2017-Chennai-deva.pdf
.. _Kindle friendly PDF: https://github.com/karthikraman/panchangam/raw/master/pdf/daily-cal-2017-Chennai-deva.pdf

"""