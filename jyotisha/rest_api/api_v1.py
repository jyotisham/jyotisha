import logging

from flask import Blueprint
import flask_restplus
from flask_restplus import Resource


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


@api.route('calendars/coordinates/<string:lattitude>/<string:longitude>/years/<string:year>')
class DailyCalendarHandler(Resource):
    get_parser = reqparse.RequestParser()
    parser.add_argument('timezone', type=string, help='Example: Asia/Calcutta', location='args', required=True)
    def get(self, p):
        args = parser.parse_args()
        timezone = args['timezone']
        city = City(city_name, latitude, longitude, timezone)
        panchangam = scripts.get_panchangam(city=city, year=year, script=script, computeLagnams=computeLagnams)

        panchangam.computeFestivals()
        panchangam.assignRelativeFestivals()
        panchangam.computeSolarEclipses()
        panchangam.computeLunarEclipses()
        panchangam.computeTransits()
        return panchangam

