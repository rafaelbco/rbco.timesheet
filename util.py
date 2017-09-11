# coding=utf8
from datetime import datetime
from datetime import timedelta
import csv
import os
from itertools import tee
from itertools import izip


def timedelta_to_str(t):
    seconds = abs(t.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return u'{}{:02d}:{:02d}'.format(
        u'' if (t.total_seconds() >= 0) else u'-',
        int(hours),
        int(minutes)
    )


def date_to_time_str(d):
    return u'{:%H:%M}'.format(d) if d else u'-'


def format_csv_dict(d):
    try:
        items = (
            (k.strip(), v.strip())
            for (k, v) in d.iteritems()
        )
        items = (
            (k, (v if (v != u'-') else None))
            for (k, v) in items
        )
        return dict(items)
    except Exception as e:
        raise RuntimeError('Exception formatting dict: {}. Error: {}'.format(d, e))


def parse_csv(path):
    with open(path, 'r') as f:
        return [format_csv_dict(i) for i in csv.DictReader(f)]


def parse_time(s, day):
    if not s:
        return None

    (hour, minute) = s.split(u':')
    return datetime(year=day.year, month=day.month, day=day.day, hour=int(hour), minute=int(minute))


def str_to_date(s):
    return datetime.strptime(s, u'%Y-%m-%d').date()


def str_to_timedelta(s):
    (hours, minutes) = s.split(u':')
    return timedelta(hours=int(hours), minutes=int(minutes))


def mkdirp(path):
    if not os.path.exists(path):
        os.makedirs(path)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
