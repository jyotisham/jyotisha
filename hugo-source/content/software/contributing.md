+++
title = "Contributing"
+++

Contributions welcome! Please see some basic comments (pertaining to the time format used internally, API layers required) in the base jyotisha package though.

## Testing and autotesting
Every push to this repository SHOULD pass tests. We should have a rich, functional set of tests at various levels. Saves everyone's time.

You can see the status of failing tests and builds at https://github.com/jyotisham/jyotisha/actions . PS: You can probably subscribe to get email notification on failed workflow runs as well - I'm getting these.

## Contact
Have a problem or question? Please head to [github](https://github.com/jyotisham/jyotisha).

## Packaging
* ~/.pypirc should have your pypi login credentials.
```
python setup.py bdist_wheel
twine upload dist/* --skip-existing
```

Test installation with one of these:
```
pip install . --target=./test_installation.local -U
pip install git+https://github.com/jyotisham/jyotisha/@master --target=./test_installation.local -U
```

## Document generation
- Sphynx html docs can be generated with `cd docs; make html` Current errors:
  - Can't find xsanscript. indic_transliteration package must be updated.
- http://jyotisha.readthedocs.io/en/latest/jyotisha.html should automatically have good updated documentation - unless there are build errors. Current build errors:
  - indic_transliteration cannot be installed. [Stackexchange question](https://stackoverflow.com/questions/45929148/read-the-docs-pip-pypi-dependency-installation-error).


## Using pyswisseph
Pyswisseph is a thin wrapper around the C++ code.

- [Official py Docs](https://astrorigin.com/pyswisseph/pydoc/index.html) - not [unsupported docs](http://pythonhosted.org/pyswisseph/swisseph-module.html).
- [swisseph docs](http://www.astro.com/swisseph/swephprg.htm)
- Install the latest library: `sudo pip3 install git+https://github.com/astrorigin/pyswisseph@master -U`

## Deployment
- [api.vedavaapi.org/jyotisha](http://api.vedavaapi.org/jyotisha)
