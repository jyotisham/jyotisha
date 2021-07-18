import logging

import flask_restplus
from flask import Blueprint
from flask_restplus import Resource
from flask_restplus import reqparse
from jyotisha.panchaanga.spatio_temporal import City, daily, annual
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.time import Timezone, Date
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, Ayanamsha
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType, Anga

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
                         description='For detailed intro and to report issues: see <a href="https://github.com/jyotisham/jyotisha">here</a>. '
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="../sitemap">sitemap</a>.',
                         default_label=api_blueprint.name,
                         prefix=URL_PREFIX, doc='/docs')


# noinspection PyUnresolvedReferences
@api.route('/calendars/coordinates/<string:latitude>/<string:longitude>/years/<string:year>')
# TODO: How to set default values for latitude and logitude here??
# Questions at: https://github.com/noirbizarre/flask-restplus/issues/381 and stackoverflow linked therein.
class DailyCalendarHandler(Resource):
  get_parser = reqparse.RequestParser()
  get_parser.add_argument('timezone', type=str, default='Asia/Calcutta', help='Example: Asia/Calcutta', location='args',
                          required=True)

  @api.expect(get_parser)
  def get(self, latitude, longitude, year):
    args = self.get_parser.parse_args()
    city = City("", latitude, longitude, args['timezone'])
    panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=int(year))

    return panchaanga.to_json_map()


# noinspection PyUnresolvedReferences
@api.route(
  '/day_length_based_periods/coordinates/<string:latitude>/<string:longitude>/years/<string:year>/months/<int:month>/days/<int:day>/')
class KaalaHandler(Resource):
  get_parser = reqparse.RequestParser()
  get_parser.add_argument('timezone', type=str, default='Asia/Calcutta', help='Example: Asia/Calcutta', location='args',
                          required=True)
  get_parser.add_argument('encoding', type=str, default='devanagari', help='Example: iso, devanagari, kannada, tamil',
                          location='args',
                          required=True)
  get_parser.add_argument('format', type=str, default='hh:mm:ss*', help='Example: hh:mm:ss*, hh:mm', location='args',
                          required=True)

  @api.expect(get_parser)
  def get(self, latitude, longitude, year, month, day):
    args = self.get_parser.parse_args()
    city = City("", latitude, longitude, args['timezone'])
    panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=int(year), month=int(month), day=int(day)))
    return panchaanga.day_length_based_periods.to_json_map()


# noinspection PyUnresolvedReferences
@api.route(
  '/timezones/<string:timezone>/times/years/<int:year>/months/<int:month>/days/<int:day>/hours/<int:hour>/minutes/<int:minute>/seconds/<int:second>/bodies/<string:body>/<string:anga_type_str>')
class DivisionFinder(Resource):
  def get(self, body_name, anga_type_str, timezone, year, month, day, hour, minute, second):
    jd = Timezone(timezone).local_time_to_julian_day(Date(year, month, day, hour, minute, second))
    nd = NakshatraDivision(jd=jd, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
    body = Graha(body_name=body_name)
    anga_type = AngaType.NAKSHATRA
    if anga_type_str == AngaType.RASHI.name:
      anga_type = AngaType.RASHI
    division = nd.get_fractional_division_for_body(body=body, anga_type=anga_type)
    logging.info(division)
    return str(division)


# noinspection PyUnresolvedReferences
@api.route(
  '/timezones/<string:timezone>/times/years/<int:year>/months/<int:month>/days/<int:day>/hours/<int:hour>/minutes/<int:minute>/seconds/<int:second>/raashi')
class RaashiFinder(Resource):
  def get(self, timezone, year, month, day, hour, minute, second):
    jd = Timezone(timezone).local_time_to_julian_day(Date(year, month, day, hour, minute, second))
    from jyotisha.panchaanga import temporal
    raashi = NakshatraDivision(jd, ayanaamsha_id=Ayanamsha.CHITRA_AT_180).get_solar_raashi()
    logging.info(raashi)
    return str(raashi)
    # return "haha"


# noinspection PyUnresolvedReferences
@api.route(
  '/timezones/<string:timezone>/times/years/<int:year>/months/<int:month>/days/<int:day>/hours/<int:hour>/minutes/<int:minute>/seconds/<int:second>/bodies/<string:body>/raashi_transition_100_days')
class RaashiTransitionFinder(Resource):
  def get(self, timezone, year, month, day, hour, minute, second, body):
    from jyotisha import zodiac
    jd = Timezone(timezone).local_time_to_julian_day(Date(year, month, day, hour, minute, second))
    from jyotisha.panchaanga import temporal
    transits = Graha.singleton(body).get_transits(jd_start=jd, jd_end=jd + 100, anga_type=AngaType.RASHI,
                                                  ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
    # logging.debug(transits)
    transits_local = [(Timezone(timezone).julian_day_to_local_time(transit.jd), transit.value_1, transit.value_2) for transit in
                      transits]
    return str(transits_local)
