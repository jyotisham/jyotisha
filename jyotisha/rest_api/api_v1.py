import logging

from flask import Blueprint
import flask_restplus
from flask_restplus import Resource

from flask_restplus import reqparse
from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam import scripts

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


@api.route('/calendars/coordinates/<string:lattitude>/<string:longitude>/years/<string:year>')
class DailyCalendarHandler(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('timezone', type=str, help='Example: Asia/Calcutta', location='args', required=True)
    get_parser.add_argument('encoding', type=str, help='Example: iast', location='args', required=True)
    @api.expect(get_parser)
    def get(self, lattitude, longitude, year):
        args = self.get_parser.parse_args()
        city = City("", lattitude, longitude, args['timezone'])
        panchangam = scripts.get_panchangam(city=city, year=int(year), script=args['encoding'])

        panchangam.computeFestivals()
        panchangam.assignRelativeFestivals()
        panchangam.computeSolarEclipses()
        panchangam.computeLunarEclipses()
        panchangam.computeTransits()
        return panchangam.to_json_map()

