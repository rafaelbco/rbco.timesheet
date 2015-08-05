# coding=utf8
from datetime import datetime
import csv
import os
from itertools import tee
from itertools import izip


def timedelta_to_str(t):
    seconds = abs(t.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return '{}{:02d}:{:02d}'.format('' if t.total_seconds() >= 0 else '-',  int(hours), int(minutes))


def date_to_time_str(d):
    return d.strftime('%H:%M') if d else '-'


def format_csv_dict(d):
    items = (
        (k.strip(), v.strip())
        for (k, v) in d.iteritems()
    )
    items = (
        (k, (v if (v != '-') else None))
        for (k, v) in items
    )
    return dict(items)


def parse_csv(path):
    with open(path, 'r') as f:
        return [format_csv_dict(i) for i in csv.DictReader(f)]


def parse_time(s, day):
    if not s:
        return None

    (hour, minute) = s.split(':')
    return datetime(year=day.year, month=day.month, day=day.day, hour=int(hour), minute=int(minute))


def mkdirp(path):
    if not os.path.exists(path):
        os.makedirs(path)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
