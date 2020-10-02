"""
A jyotiSha computation package!

A note on time: We internally use julian dates in the UTC time scale (See wiki article: https://en.wikipedia.org/wiki/Time_standard ). This is different from the Terrestrial time (TT), which contuines from the former Ephemeris time(ET) standard.

Note on swiss ephemeris API: Please don't call it directly - there should always a layer inbetween the ephemeris API and our logic. This wrapper layer is located in the packages temporal, spatio_temporal, graha and zodiac. Using this wrapper allows us to easily adjust to ephemeris API changes, and to ensure correctness (eg. sending time in UTC rather than ET time scale).

Note on storing variables: Please remember that most objects here (including panchAnga-s) are serialized as JSON objects. That means that you CANNOT (re)store python dictionaries with numeric keys. Please don't do that. Use plain arrays of arrays if you must.

Note on core vs peripheral parts of the code: Please don't put your custom tex/ md/ ics whatever code in core code and pollute core library functions. Wrap them in your own functions if you must. Functions should be atomic.
"""
