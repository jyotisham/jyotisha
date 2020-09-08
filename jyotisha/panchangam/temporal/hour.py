import logging
import math
import traceback
from math import modf

from sanskrit_data.schema.common import JsonObject


class Hour(JsonObject):

    """This  class is a time class with methods for printing, conversion etc.
    """

    def __init__(self, hour):
        super().__init__()
        if type(hour) == float or type(hour) == int:
            self.hour = hour
        else:
            raise(TypeError('Input to time class must be int or float!'))

    def toString(self, default_suffix='', format='hh:mm', rounding=False):
        if self.hour < 0:
          logging.error('t<0! %s ' % self.hour)
          logging.error(traceback.print_stack())

        msec, secs = modf(self.hour * 3600)
        msec = round(msec * 1000)
        if msec == 1000:
          msec = 0
          secs += 1

        hour = secs // 3600
        secs = secs % 3600

        suffix = default_suffix
        if format[-1] == '*':
          if hour >= 24:
              suffix = '*'
        else:
          if hour >= 24:
              hour -= 24
              suffix = '(+1)'  # Default notation for times > 23:59

        minute = secs // 60
        secs = secs % 60
        second = secs

        if format in ('hh:mm', 'hh:mm*'):
          # Rounding done if 30 seconds have elapsed
          return '%02d:%02d%s' % (hour, minute + ((secs + (msec >= 500)) >= 30) * rounding, suffix)
        elif format in ('hh:mm:ss', 'hh:mm:ss*'):
          # Rounding done if 500 milliseconds have elapsed
          return '%02d:%02d:%02d%s' % (hour, minute, second + (msec >= 500) * rounding, suffix)
        elif format in ('hh:mm:ss.sss', 'hh:mm:ss.sss*'):
          return '%02d:%02d:%02d.%03d%s' % (hour, minute, second, msec, suffix)
        elif format == 'gg-pp':  # ghatika-pal
          secs = round(self.hour * 3600)
          gg = secs // 1440
          secs = secs % 1440
          pp = secs // 24
          return ('%d-%d' % (gg, pp))
        elif format == 'gg-pp-vv':  # ghatika-pal-vipal
          vv_tot = round(self.hour * 3600 / 0.4)
          logging.debug(vv_tot)
          vv = vv_tot % 60
          logging.debug(vv)
          vv_tot = (vv_tot - vv) // 60
          logging.debug(vv_tot)
          pp = vv_tot % 60
          logging.debug(pp)
          vv_tot = (vv_tot - pp) // 60
          logging.debug(vv_tot)
          gg = vv_tot
          logging.debug(gg)
          return ('%d-%d-%d' % (gg, pp, vv))
        else:
          raise Exception("""Unknown format""")

    def __str__(self):
        return self.toString(format='hh:mm:ss')


def decypher_fractional_hours(time_in_hours):
    minutes, _ = modf(time_in_hours * 60)
    seconds, minutes = modf(minutes * 60)
    return (int(time_in_hours), int(minutes), seconds)