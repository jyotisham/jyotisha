import logging

from flask import Blueprint
import flask_restplus
from flask_restplus import Resource

from flask_restplus import reqparse
from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam import scripts
import swisseph as swe

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(
  'panchanga', __name__,
  template_folder='templates'
)

api = flask_restplus.Api(app=api_blueprint, version='1.0', title='jyotisha panchanga API',
                         description='For detailed intro and to report issues: see <a href="https://github.com/sanskrit_coders/jyotisha">here</a>. '
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="../sitemap">sitemap</a>.',
                         default_label=api_blueprint.name,
                         prefix=URL_PREFIX, doc='/docs')


# noinspection PyUnresolvedReferences
@api.route('/calendars/coordinates/<string:lattitude>/<string:longitude>/years/<string:year>')
class DailyCalendarHandler(Resource):
  get_parser = reqparse.RequestParser()
  get_parser.add_argument('timezone', type=str, help='Example: Asia/Calcutta', location='args', required=True)
  get_parser.add_argument('encoding', type=str, help='Example: iast, devanagari, kannada, tamil', location='args',
                          required=True)

  @api.expect(get_parser)
  def get(self, lattitude, longitude, year):
    args = self.get_parser.parse_args()
    city = City("", lattitude, longitude, args['timezone'])
    panchangam = scripts.get_panchangam(city=city, year=int(year), script=args['encoding'])

    panchangam.compute_festivals()
    panchangam.assign_relative_festivals()
    panchangam.compute_solar_eclipses()
    panchangam.compute_lunar_eclipses()
    panchangam.computeTransits()
    return panchangam.to_json_map()


# noinspection PyUnresolvedReferences
@api.route('/nakshatras/utc_offsets/<string:offset>/years/<int:year>/months/<int:month>/days/<int:day>/hours/<int:hour>/minutes/<int:minute>/seconds/<int:second>/bodies/<string:body>')
class NakshatraFinder(Resource):
  def get(self, body, offset, year, month, day, hour, minute, second):
    from jyotisha import zodiac
    (utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second) = swe.utc_time_zone(year, month, day, hour, minute, second, float(offset))
    julday = swe.utc_to_jd(year=utc_year, month=utc_month, day=utc_day, hour=utc_hour, minutes=utc_minute, seconds=utc_second, flag=1)[0]
    lahiri_nakshatra_division = zodiac.NakshatraDivision(julday=julday)
    body_id = -1
    if body == "sun":
      body_id = swe.SUN
    elif body == "moon":
      body_id = swe.MOON
      from jyotisha.panchangam import temporal
      logging.debug(temporal.get_nakshatram(julday))
    nakshatra = lahiri_nakshatra_division.get_nakshatra(body_id=body_id)
    logging.info(nakshatra)
    return str(nakshatra)
    # return "haha"


# noinspection PyUnresolvedReferences
@api.route('/raashis/utc_offsets/<string:offset>/years/<int:year>/months/<int:month>/days/<int:day>/hours/<int:hour>/minutes/<int:minute>/seconds/<int:second>')
class RaashiFinder(Resource):
  def get(self, offset, year, month, day, hour, minute, second):
    (utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second) = swe.utc_time_zone(year, month, day, hour, minute, second, float(offset))
    julday = swe.utc_to_jd(year=utc_year, month=utc_month, day=utc_day, hour=utc_hour, minutes=utc_minute, seconds=utc_second, flag=1)[0]
    from jyotisha.panchangam import temporal
    raashi = temporal.get_solar_rashi(jd=julday)
    logging.info(raashi)
    return str(raashi)
    # return "haha"