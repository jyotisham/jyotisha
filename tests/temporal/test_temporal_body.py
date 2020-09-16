import logging

from jyotisha.panchangam.temporal import body

from jyotisha.panchangam.temporal.body import Graha


logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def test_get_longitude():
    assert Graha(Graha.SUN).get_longitude(jd=2458434.083333251) == 229.12286985575702


def test_get_star_longitude():
    assert body.get_star_longitude(star="Spica", jd=2458434.083333251) == 204.09485939669307