#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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
-  Python: pyswisseph, SciPy, icalendar and pytz
-  XeLaTeX / fontspec and a few other ‘regular’ packages
-  Fonts: Sanskrit 2003, Candara, Vijaya (for Tamil)

Usage
-----

Helper scripts
~~~~~~~~~~~~~~
See https://github.com/karthikraman/panchangam repository.



Documentation & References
--------------------------

Currently, the documentation is sparse, but I hope to populate more in
the ``docs`` folder. There are also some useful references in the
``docs/ref`` folder.

Downloadable Panchangams (PDF/ICS)
----------------------------------
See https://github.com/karthikraman/panchangam repository.


Similar software
-----------------

-  `drik-panchanga`_: well-written Python-based panchangam, with a nice
   simple GUI
-  `drikpanchang.com`_: online calendar, with a lot of details,
   festivals etc.

.. _drik-panchanga: https://github.com/webresh/drik-panchanga
.. _drikpanchang.com: https://www.drikpanchang.com


Credits
-------

Sincere thanks to the creators of pyswisseph, without which I could not
have attempted this. Many thanks are due to `Ajit Krishnan`_ for so
clearly explaining the panchangam process, and example festivals, which
was sort of the inspiration for integrating a number of festivals. Many
thanks to Saketha Nath for getting details of hundreds of festivals from
obscure sources, and to the `Vaidikasri magazine`_, which is another
veritable treasure house of these festivals.

.. _Ajit Krishnan: http://aupasana.com/
.. _Vaidikasri magazine: http://vaithikasri.com/


Disclaimer
----------

It is very important to note that this is an *approximate* panchangam,
automatically generated, without the careful oversight of learned
scholars who have the depth of knowledge to resolve the exact dates for
occurrences of different festivals. Also, the ayanamsha used here
conforms to the Drik panchanga. The best use of this panchangam is as an
approximate guide (95% of the events are also probably spot on) — when
in doubt, consult only your own panchangam!

Bugs
~~~~

I have not extensively tested the code, especially for Southern
Hemisphere locations etc. I have primarily restricted my example testing
to Chennai, Mumbai, London and Palo Alto. Please let me know of any bugs
or errors that you encounter by raising an issue and I’ll do my best to
fix them. I wish I had the time to rewrite the whole thing efficiently;
there are far too many vestiges of the old code built on my then novice
Python knowledge!

"""