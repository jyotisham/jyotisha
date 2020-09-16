"""
A jyotiSha computation package!

A note on time: We internally use julian dates in the UTC time scale (See wiki article: https://en.wikipedia.org/wiki/Time_standard ). This is different from the Terrestrial time (TT), which contuines from the former Ephemeris time(ET) standard.

Note on swiss ephemeris API: Please don't call it directly - there should always a layer inbetween the ephemeris API and our logic. This wrapper layer is located in the packages temporal, spatio_temporal, graha and zodiac. Using this wrapper allows us to easily adjust to ephemeris API changes, and to ensure correctness (eg. sending time in UTC rather than ET time scale).
"""
