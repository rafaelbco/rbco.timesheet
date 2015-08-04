# coding=utf8
from datetime import datetime
import csv
import os


def timedelta_to_str(t):
    seconds = abs(t.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return '{:02d}:{:02d}'.format(int(hours), int(minutes))


def date_to_time_str(d):
    return d.strftime('%H:%M') if d else '-'


def format_csv_dict(d):
    return {k.strip(): v.strip() for (k, v) in d.iteritems()}


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
