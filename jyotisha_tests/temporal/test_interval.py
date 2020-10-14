from jyotisha.panchaanga.temporal import interval
from jyotisha.panchaanga.temporal.interval import Interval


def test_get_interval():
  assert interval.get_interval(start_jd=1, end_jd=11, part_index=[0], num_parts=1) == Interval(jd_start=1, jd_end=11)