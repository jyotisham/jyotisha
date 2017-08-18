JyotiSha tools
==============
# For users
For detailed examples and help, please see individual module files in this package.

## Installation or upgrade:
* `sudo pip2 install jyotisha -U`
* `sudo pip2 install git+https://github.com/sanskrit-coders/jyotisha/@master -U`
* [Web](https://pypi.python.org/pypi/jyotisha).

# For contributors
## Contact
Have a problem or question? Please head to [github](https://github.com/sanskrit-coders/jyotisha).

## Packaging
* ~/.pypirc should have your pypi login credentials.
```
python setup.py bdist_wheel
twine upload dist/* --skip-existing
```