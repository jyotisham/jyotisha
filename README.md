JyotiSha tools and data
=======================
[![PyPI version](https://badge.fury.io/py/jyotisha.svg)](https://badge.fury.io/py/jyotisha)
[![Documentation Status](https://readthedocs.org/projects/jyotisha/badge/?version=latest)](https://jyotisha.readthedocs.io/en/latest/?badge=latest)
[![Actions Status](https://github.com/sanskrit-coders/jyotisha/workflows/Python%20package/badge.svg)](https://github.com/sanskrit-coders/jyotisha/actions)

## Intro
A package to do various panchaanga (traditional vedic astronomical / astrological) calculations, produce calendars.

## For users
For detailed examples and help, please see individual module files in this package.

### Installation or upgrade:
- Install the pyswisseph library specially as described below.
- Install the jyotisha package
  -  (Prefer this to get the latest code:)`sudo pip install git+https://github.com/sanskrit-coders/jyotisha/@master -U`
  - `sudo pip install jyotisha -U`
- [Web](https://pypi.python.org/pypi/jyotisha).

### Usage
- REST API/ swagger web interface 
    - Deployments at [vedavaapi](http://api.vedavaapi.org/jyotisha).
- Please see the generated python sphynx docs in one of the following places:
    - http://jyotisha.readthedocs.io [Broken as of 20170828.]
    - [project page](https://sanskrit-coders.github.io/jyotisha/build/html/jyotisha.html).
    - under docs/_build/html/index.html
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