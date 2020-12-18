+++
title = "For users"
+++

For detailed examples and help, please see individual module files - especially test files in this package.

## Installation or upgrade:
- Install the pyswisseph library specially as described below.
- Install the jyotisha package
  -  (Prefer this to get the latest code:)`sudo pip install git+https://github.com/jyotisham/jyotisha/@master -U`
  - `sudo pip install jyotisha -U`
- [Web](https://pypi.python.org/pypi/jyotisha).

## Usage
### Simple invocation
- The simplest way to invoke the code and generate calendars in a variety of forms (icalendar/ ics, tex [which can then be converted to pdf], markdown [which can then be presented as html]) is to use python invocations of the type seen in:
  - tests such as those in [jyotisha_tests/spatio_temporal/writer](https://github.com/jyotisham/jyotisha/tree/master/jyotisha_tests/spatio_temporal/writer)
  - Calendar generation projects such as those under this folder - [jyotisha/panchaanga/writer/generation_project](https://github.com/jyotisham/jyotisha/tree/master/jyotisha/panchaanga/writer/generation_project)
- Command line usage - can be invoked via some shell scripts at [karthik's panchaanga repo](https://github.com/karthikraman/panchangam). But these often go out of date - so you might need to debug them. See [this issue](https://github.com/jyotisham/jyotisha/issues/10).

### API usage
- Please see the generated python sphynx docs in one of the following places (jyotisha.panchanga.scripts package docs may be particularly relevant):
    - [readthedocs site](http://jyotisha.readthedocs.io)
    - under docs/_build/html/index.html
- REST API/ swagger web interface 
    - Deployments at [vedavaapi](http://api.vedavaapi.org/jyotisha) - obsolete and unmaintained as of 2020.

## Calendars produced
- See [this site](https://jyotisham.github.io/jyotisha/output/) [To generate basic website locally, run `cd docs;bundle exec jekyll serve`] - includes some markdown → html and ics calendars.

