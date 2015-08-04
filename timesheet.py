# coding=utf8
"""Process time sheets.

Usage:
  timesheet [options] <db_path> <out_path>

Options:
  -h, --help          Imprime esta mensagem.
"""
from docopt import docopt
import os
import re
import csv
from rbco.caseclasses import case
from datetime import date
from datetime import datetime
from datetime import timedelta
import shutil
import calendar


YEAR_DIR_PATTERN = re.compile(r'^\d\d\d\d$')
MONTH_FILE_PATTERN = re.compile(r'^\d\d\.csv$')
DAY_HEADER_TEMPLATE = '    '.join([
    '{:<3}'.format('day'),
    '{:<5}'.format('type'),
    '{:<5}'.format('in'),
    '{:<5}'.format('out'),
    '{:<10}'.format('worked'),
    '{:<10}'.format('balance'),

])
DAY_LINE_TEMPLATE = '    '.join([
    '{day:%d} ',
    '{day_type:<5}',
    '{checkin:<5}',
    '{checkout:<5}',
    '{worked:<10}',
    '{balance:<10}',
])


@case
class DayRecord(object):

    valid_day_types = ('N', 'WE', 'H', 'V')

    def __init__(self, day, day_type, checkin, checkout):
        pass

    def worked(self):
        return (
            self.checkout - self.checkin
            if (self.checkin and self.checkout)
            else timedelta(0)
        )

    def validate(self):
        errors = []
        if self.day_type not in self.valid_day_types:
            errors.append('Invalid day_type.')

        if self.checkin and (not self.checkout):
            errors.append('Checkin without checkout.')

        if (not self.checkin) and self.checkout:
            errors.append('Checkout without checkin.')

        if self.checkin and self.checkout and (self.checkout < self.checkin):
            errors.append('Checkout before checkin.')

        return errors


@case
class MonthRecord(object):

    def __init__(self, year, month, day_records):
        pass

    def worked(self):
        return sum((d.worked() for d in self.day_records), timedelta(0))

    def validate(self):
        errors = [(d, d.validate()) for d in self.day_records]
        errors = [
            '{}: {}'.format(d.day.day, ' / '.join(e))
            for (d, e)
            in errors
            if e
        ]
        start_day = 1
        end_day = calendar.monthrange(self.year, self.month)[1]
        for i in xrange(start_day, end_day + 1):
            if not self.get_day_record(i):
                errors.append('Missing day: {}.'.format(i))


@case
class YearRecord(object):

    def __init__(self, year, month_records):
        pass

    def worked(self):
        return sum((m.worked() for m in self.month_records), timedelta(0))

    def validate(self):
        errors = []
        for m in self.month_records:
            for e in m.validate():
                errors.append('{}: {}'.format(m.month, e))

        return errors


class DB(object):

    def __init__(self, year_records=None):
        self.year_records = year_records or []

    def worked(self):
        return sum((y.worked() for y in self.year_records), timedelta(0))

    def validate(self):
        errors = []
        for y in self.year_records:
            for e in y.validate():
                errors.append('{}: {}'.format(y.year, e))

        return errors

    def print_db(self):
        for year_record in self.year_records:
            print 'Year: {}, worked: {}'.format(year_record.year, year_record.worked())
            print

            for month_record in year_record.month_records:
                print 'Month: {}, worked: {}'.format(month_record.month, month_record.worked())
                print

                for day_record in month_record.day_records:
                    print day_record, day_record.worked()

    def load(self, path):
        year_dirs = sorted(
            i for i in os.listdir(path)
            if YEAR_DIR_PATTERN.match(i) is not None
        )

        for year_dir in year_dirs:
            year = int(year_dir)
            year_path = os.path.join(path, year_dir)
            month_files = sorted(
                i for i in os.listdir(year_path)
                if MONTH_FILE_PATTERN.match(i) is not None
            )

            year_record = YearRecord(year=year, month_records=[])
            self.year_records.append(year_record)

            for month_file in month_files:
                month = int(month_file.split('.')[0])
                month_path = os.path.join(year_path, month_file)
                days = parse_month_file(month_path, year=year)
                month_record = MonthRecord(year=year, month=month, day_records=days)
                year_record.month_records.append(month_record)


@case
class Policy(object):

    def __init__(self, hours_per_day):
        pass

    def day_balance(self, day_record):
        return (
            (day_record.worked() - timedelta(hours=self.hours_per_day))
            if (day_record.day_type == 'N')
            else timedelta(0)
        )

    def month_balance(self, month_record):
        return sum((self.day_balance(d) for d in month_record.day_records), timedelta(0))

    def year_balance(self, year_record):
        return sum((self.month_balance(m) for m in year_record.month_records), timedelta(0))

    def db_balance(self, db):
        return sum((self.year_balance(m) for m in db.year_records), timedelta(0))


DEFAULT_POLICY = Policy(hours_per_day=7)


def report(db, policy, path):
    if os.path.exists(path):
        shutil.rmtree(path)
    mkdirp(path)

    with open(os.path.join(path, 'totals.txt'), 'w') as f:
        print >> f, 'Worked: {}'.format(timedelta_to_str(db.worked()))
        print >> f, 'Balance: {}'.format(timedelta_to_str(policy.db_balance(db)))

    for year_record in db.year_records:
        year_path = os.path.join(path, str(year_record.year))
        mkdirp(year_path)

        with open(os.path.join(year_path, 'totals.txt'), 'w') as f:
            print >> f, 'Worked: {}'.format(timedelta_to_str(year_record.worked()))
            print >> f, 'Balance: {}'.format(timedelta_to_str(policy.year_balance(year_record)))

        for month_record in year_record.month_records:
            month_path = os.path.join(year_path, '{:02d}.txt'.format(month_record.month))

            with open(month_path, 'w') as f:
                print >> f, DAY_HEADER_TEMPLATE
                for day_record in month_record.day_records:
                    print >> f, day_record_to_report_line(day_record, policy)

                print >> f, 'Worked: {}'.format(timedelta_to_str(month_record.worked()))
                month_balance = timedelta_to_str(policy.month_balance(month_record))
                print >> f, 'Balance: {}'.format(month_balance)

    print timedelta_to_str(policy.db_balance(db))


def day_record_to_report_line(day_record, policy):
    return DAY_LINE_TEMPLATE.format(
        day=day_record.day,
        day_type=day_record.day_type,
        checkin=day_record.checkin.strftime('%H:%M') if day_record.checkin else '-',
        checkout=day_record.checkout.strftime('%H:%M') if day_record.checkout else '-',
        worked=timedelta_to_str(day_record.worked()),
        balance=timedelta_to_str(policy.day_balance(day_record)),
    )


def timedelta_to_str(t):
    seconds = abs(t.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return '{:02d}:{:02d}'.format(int(hours), int(minutes))


def main():
    arguments = docopt(__doc__)

    db_path = arguments['<db_path>']
    out_path = arguments['<out_path>']

    db = DB()
    db.load(db_path)
    db.print_db()
    print

    for e in db.validate():
        print e
    print

    report(db, DEFAULT_POLICY, out_path)


def parse_month_file(path, year):
    month = int(os.path.basename(path).split('.')[0])

    with open(path, 'r') as f:
        dicts = [_format_dict(i) for i in csv.DictReader(f)]

    day_records = []
    for d in dicts:
        day = date(year=year, month=month, day=int(d['day']))
        day_records.append(DayRecord(
            day=day,
            day_type=d['day_type'],
            checkin=_parse_time(d['checkin'], day),
            checkout=_parse_time(d['checkout'], day),
        ))

    return day_records


def _format_dict(d):
    return {k.strip(): v.strip() for (k, v) in d.iteritems()}


def _parse_time(s, day):
    if not s:
        return None

    (hour, minute) = s.split(':')
    return datetime(year=day.year, month=day.month, day=day.day, hour=int(hour), minute=int(minute))


def mkdirp(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == '__main__':
    main()
