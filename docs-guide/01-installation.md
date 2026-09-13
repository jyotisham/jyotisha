# Installation

## 1. Install `pyswisseph` first, carefully

`jyotisha`'s ephemeris computations are built on the
[Swiss Ephemeris](https://www.astro.com/swisseph/swephprg.htm) C library, wrapped by the
`pyswisseph` PyPI package (imported in code as `swisseph`, *not* `pyswisseph`). This is a
compiled extension, and it's the dependency most likely to give you trouble:

- `requirements.txt` pins an exact version: `pyswisseph==2.10.3.2`. If you `pip install`
  a different version, `import swisseph` may still work but some of the swiss-ephemeris
  data files bundled under `jyotisha/panchaanga/temporal/data` may not match what that
  version expects (this is a known, documented gotcha — see
  `hugo-source/content/software/contributing.md`).
- If `pip install pyswisseph` fails to build from source, you need a C compiler toolchain
  present (`build-essential` on Debian/Ubuntu, Xcode command line tools on macOS).

## 2. Install jyotisha itself

```bash
# Latest code (recommended over the PyPI release, which lags):
pip install git+https://github.com/jyotisham/jyotisha/@master -U

# Or the released package:
pip install jyotisha -U
```

If you're working on jyotisha itself (this checkout), install it editable together with
its pinned requirements:

```bash
pip install -r requirements.txt
pip install -e .
```

## 3. Festival data is a git submodule — initialize it

Festival rule data (thousands of `.toml` files — see
[06-festivals.md](06-festivals.md)) lives in a separate repo
([`adyatithi`](https://github.com/jyotisham/adyatithi)), vendored as a git submodule at
`jyotisha/panchaanga/temporal/festival/data`. If you cloned this repo without
`--recurse-submodules`, that directory will be empty and any computation that needs
festivals (i.e. anything beyond a bare `DailyPanchaanga`) will silently return zero
festivals rather than erroring. Initialize it with:

```bash
git submodule update --init --recursive
```

## 4. Sanity-check your install

```python
import logging
logging.disable(logging.CRITICAL)  # jyotisha's modules configure root DEBUG logging on import — quiet it

from jyotisha.panchaanga.spatio_temporal import City, daily
from jyotisha.panchaanga.temporal.time import Date

city = City.get_city_from_db("Chennai")
panchaanga = daily.DailyPanchaanga(city=city, date=Date(2024, 1, 15))
print(panchaanga.jd_sunrise)   # -> 2460324.547738522 (a Julian day number)
```

If that prints a Julian day number (a float around 2.46 million) without raising
`ModuleNotFoundError: No module named 'swisseph'`, your install is good — move on to
[02-quickstart.md](02-quickstart.md).

### Pitfall: the logging setup

Several jyotisha modules call `logging.basicConfig(level=logging.DEBUG, ...)` at import
time. Because `logging.basicConfig` is a no-op after the first call in a process, whoever
imports first "wins" — but in practice this means importing almost anything from
`jyotisha.panchaanga` turns on root DEBUG logging for your whole process, including
noisy per-degree ephemeris search logs. Call `logging.disable(logging.CRITICAL)` (or
configure logging yourself *before* importing jyotisha) if you don't want that.
