JyotiSha tools and data
=======================
[![PyPI version](https://badge.fury.io/py/jyotisha.svg)](https://badge.fury.io/py/jyotisha)
[![Documentation Status](https://readthedocs.org/projects/jyotisha/badge/?version=latest)](https://jyotisha.readthedocs.io/en/latest/?badge=latest)
[![Actions Status](https://github.com/sanskrit-coders/jyotisha/workflows/Python%20package/badge.svg)](https://github.com/sanskrit-coders/jyotisha/actions)

## Intro
A package to do various panchaanga (traditional vedic astronomical / astrological) calculations, produce calendars. It is backed by the pretty big [adyatithi events database](https://github.com/sanskrit-coders/adyatithi).

The code itself is capable of typical (amAnta, chitra-at-180 ayanAMsha, असङ्क्रान्तिमासोऽधिकः ) based calculation (which can be invoked via some shell scripts at [karthik's panchaanga repo](https://github.com/karthikraman/panchangam) ) as well as the ancient but now uncommon [tropical lunisolar system](https://vvasuki.github.io/jyotiSham/history/kauNDinyAyana/). 

For a survey of similar software, see [here](https://sanskrit-coders.github.io/astronomy/).

### Accuracy status
It is very important to note that this is an *approximate* panchaanga,
automatically generated, without the careful oversight of learned
scholars who have the depth of knowledge to resolve the exact dates for
occurrences of different festivals. The best use of this panchaanga is as an
approximate guide (95% of the events are also probably spot on) — when
in doubt, consult only your own panchaanga!

Kartik has primarily restricted his testing to Chennai, Mumbai, London and Palo Alto.

### Development status
From vvasuki: "Despite recent MAJOR code cleanup/ testing/ structuring efforts, because of (rather unexpected) [speed](https://github.com/sanskrit-coders/jyotisha/issues/52) and portability concerns, I favor moving to a better language. I've started a multiplatform-targetted Kotlin project at [jyotisha-kotlin](https://github.com/sanskrit-coders/jyotisha-kotlin) ."

## For users
For detailed examples and help, please see individual module files - especially test files in this package.

### Installation or upgrade:
- Install the pyswisseph library specially as described below.
- Install the jyotisha package
  -  (Prefer this to get the latest code:)`sudo pip install git+https://github.com/sanskrit-coders/jyotisha/@master -U`
  - `sudo pip install jyotisha -U`
- [Web](https://pypi.python.org/pypi/jyotisha).

### Usage
- Please see the generated python sphynx docs in one of the following places (jyotisha.panchanga.scripts package docs may be particularly relevant):
    - http://jyotisha.readthedocs.io [Broken as of 20170828.]
    - Rarely updated [project page](https://sanskrit-coders.github.io/jyotisha/build/html/jyotisha.html).
    - under docs/_build/html/index.html
- REST API/ swagger web interface 
    - Deployments at [vedavaapi](http://api.vedavaapi.org/jyotisha) - obsolete and unmaintained as of 2020.
- Command line usage - See [this issue](https://github.com/sanskrit-coders/jyotisha/issues/10).

## For contributors
Contributions welcome! Please see some basic comments (pertaining to the time format used internally, API layers required) in the base jyotisha package though.

### Testing and autotesting
Every push to this repository SHOULD pass tests. We should have a rich, functional set of tests at various levels. Saves everyone's time.

You can see the status of failing tests and builds at https://github.com/sanskrit-coders/jyotisha/actions . PS: You can probably subscribe to get email notification on failed workflow runs as well - I'm getting these.

### Contact
Have a problem or question? Please head to [github](https://github.com/sanskrit-coders/jyotisha).

### Packaging
* ~/.pypirc should have your pypi login credentials.
```
python setup.py bdist_wheel
twine upload dist/* --skip-existing
```

Test installation with one of these:
```
pip install . --target=./test_installation.local -U
pip install git+https://github.com/sanskrit-coders/jyotisha/@master --target=./test_installation.local -U
```

### Document generation
- Sphynx html docs can be generated with `cd docs; make html` Current errors:
  - Can't find xsanscript. indic_transliteration package must be updated.
- http://jyotisha.readthedocs.io/en/latest/jyotisha.html should automatically have good updated documentation - unless there are build errors. Current build errors:
  - indic_transliteration cannot be installed. [Stackexchange question](https://stackoverflow.com/questions/45929148/read-the-docs-pip-pypi-dependency-installation-error).


### Using pyswisseph
Pyswisseph is a thin wrapper around the C++ code.

- [Official py Docs](https://astrorigin.com/pyswisseph/pydoc/index.html) - not [unsupported docs](http://pythonhosted.org/pyswisseph/swisseph-module.html).
- [swisseph docs](http://www.astro.com/swisseph/swephprg.htm)
- Install the latest library: `sudo pip3 install git+https://github.com/astrorigin/pyswisseph@master -U`

### Deployment
- [api.vedavaapi.org/jyotisha](http://api.vedavaapi.org/jyotisha)


## Credits

Sincere thanks to the creators of pyswisseph, without which I could not
have attempted this. Many thanks are due to [Ajit Krishnan][] for so
clearly explaining the panchaanga process, and example festivals, which
was sort of the inspiration for integrating a number of festivals. Many
thanks to Saketha Nath for getting details of hundreds of festivals from
obscure sources, and to the [Vaidikasri magazine][], which is another
veritable treasure house of these festivals.

  [Ajit Krishnan]: http://aupasana.com/
  [Vaidikasri magazine]: http://vaithikasri.com/