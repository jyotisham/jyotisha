+++
title = "For users"
+++

For detailed examples and help, please see individual module files - especially test files in this package.

## Installation or upgrade:
- Install the pyswisseph library specially as described in the [contribution section](../contributing/).
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

#### Sample code to output panchaanga
```python
# Produce a panchaanga
from jyotisha.panchaanga.spatio_temporal import City, annual, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.time import Date
city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=2021, computation_system=ComputationSystem.TEST, allow_precomputed=False)

## Markdown
from jyotisha.panchaanga.writer import md
from doc_curation.md.file import MdFile
md_file = MdFile(file_path="/some/path.md")
md_file.dump_to_file(metadata={"title": str(2019)}, content=md.make_md(panchaanga=panchaanga), dry_run=False)

## Tex
from jyotisha.panchaanga.writer.tex.daily_tex_writer import emit
from indic_transliteration import sanscript
emit(panchaanga,
     output_stream=open("/some/path.tex", 'w'), languages=["sa", "ta"], scripts=[sanscript.DEVANAGARI, sanscript.TAMIL])

## ICS
from jyotisha.panchaanga.writer import ics
ics_calendar = ics.compute_calendar(panchaanga)
ics.write_to_file(ics_calendar, "/some/path.ics")
```

Note that there are several "ComputationalSystem" options.  
Please see jyotisha/panchaanga/temporal/__init__.py .  
Particularly, lunar month assignment can be sidereal (luni-solar) or tropical, pUrNImAnta or amAnta.  
One can also select the festival cateogries to enable or disable; pick a different "ayanAMsha" (for setting naxatra boundaries).

### API usage
- Please look at the [test cases](https://github.com/jyotisham/jyotisha/tree/master/jyotisha_tests) - they are your best guide for how to do stuff like getting panchAnga for a day.
- Please see the generated python sphynx docs in one of the following places (jyotisha.panchanga.scripts package docs may be particularly relevant):
    - [readthedocs site](http://jyotisha.readthedocs.io)
    - under docs/_build/html/index.html
- REST API/ swagger web interface 
    - Deployments at [vedavaapi](http://api.vedavaapi.org/jyotisha) - obsolete and unmaintained as of 2020.

## Calendars produced
- See [this site](https://jyotisham.github.io/jyotisha/output/) [To generate basic website locally, run `cd docs;bundle exec jekyll serve`] - includes some markdown → html and ics calendars.

