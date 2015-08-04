# coding=utf8
"""Process time sheets.

Usage:
  timesheet [options] <db_path> <out_path>

Options:
  -h, --help          Print this help text.
"""
from datetime import date
from datetime import datetime
from datetime import timedelta
from docopt import docopt
import calendar
import csv
import os
import re
import shutil


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


class Record(object):
    u"""Interface for records representing a period of time in a timesheet."""

    def worked(self):
        u"""Return a `timedelta` representing the amount of time worked in the period."""
        raise NotImplementedError()

    def validate(self):
        u"""Validate the record.

        Return: a sequence of error messages or an empty sequence if the record is ok
        """
        raise NotImplementedError()

    def identifier(self):
        u"""Return an unique string which identifies the record."""
        raise NotImplementedError()


class CompositeRecord(Record):
    u"""Base class for records which are a composition of other `Record` instances.

    Subclasses must implement a `records` attribute containing a sequence of `Record`.
    """

    def worked(self):
        u"""Implement `Record`."""
        return sum((r.worked() for r in self.records), timedelta(0))

    def validate(self):
        u"""Implement `Record`."""
        record_errors = ((r, r.validate()) for r in self.records)
        record_errors = ((r, e) for (r, e) in record_errors if e)
        errors = []
        for (r, r_errors) in record_errors:
            for e in r_errors:
                errors.append('{}: {}'.format(r.identifier(), e))

        return errors


class DayRecord(Record):

    valid_day_types = ('N', 'WE', 'H', 'V')

    def __init__(self, day, day_type, checkin, checkout):
        self.day = day
        self.day_type = day_type
        self.checkin = checkin
        self.checkout = checkout

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

    def identifier(self):
        return self.day.strftime('%y-%m-%d')

    def __str__(self):
        return '{}: {:<5} {:<5} {:<5}'.format(
            self.identifier(),
            self.day_type,
            date_to_time_str(self.checkin),
            date_to_time_str(self.checkout)
        )


class MonthRecord(CompositeRecord):

    def __init__(self, year, month, records=None):
        self.year = year
        self.month = month
        self.records = records if (records is not None) else []

    def validate(self):
        errors = CompositeRecord.validate(self)

        start_day = 1
        last_day_of_month = calendar.monthrange(self.year, self.month)[1]
        today = date.today()
        end_day = min([today.day, last_day_of_month])

        for r in self.records:
            if (r.day.year != self.year) or (r.day.month != self.month):
                errors.append('Record belongs to another month: {}'.format(r.identifier()))

        for i in xrange(start_day, end_day + 1):
            if not self.get_day_record(i):
                errors.append('Missing day: {}.'.format(i))

        return errors

    def get_day_record(self, day_number):
        for r in self.records:
            if r.day.day == day_number:
                return r

        return None

    def identifier(self):
        return '{}-{:02d}'.format(self.year, self.month)


class YearRecord(CompositeRecord):

    def __init__(self, year, records=None):
        self.year = year
        self.records = records if (records is not None) else []

    def identifier(self):
        return str(self.year)


class TimeSheet(CompositeRecord):

    def __init__(self, records=None):
        self.records = records if (records is not None) else []

    def identifier(self):
        return 'timesheet'

    def print_timesheet(self):
        for year_record in self.records:
            print 'Year: {}, worked: {}'.format(
                year_record.year,
                timedelta_to_str(year_record.worked())
            )
            print

            for month_record in year_record.records:
                print 'Month: {}, worked: {}'.format(
                    month_record.month,
                    timedelta_to_str(month_record.worked())
                )
                print

                for day_record in month_record.records:
                    print day_record, timedelta_to_str(day_record.worked())

    def load(self, path):
        year_dirs = sorted(
            i for i in os.listdir(path)
            if YEAR_DIR_PATTERN.match(i) is not None
        )
        self.records = [
            self.parse_year(os.path.join(path, year_dir))
            for year_dir
            in year_dirs
        ]

    def parse_year(self, year_path):
        year = int(os.path.basename(year_path))
        month_files = sorted(
            i for i in os.listdir(year_path)
            if MONTH_FILE_PATTERN.match(i) is not None
        )

        return YearRecord(
            year=year,
            records=[
                self.parse_month(os.path.join(year_path, month_file), year)
                for month_file in month_files
            ]
        )

    def parse_month(self, month_path, year):
        month = int(os.path.basename(month_path).split('.')[0])
        dicts = parse_csv(month_path)
        return MonthRecord(
            year=year,
            month=month,
            records=[
                self._day_dict_from_csv_to_day_record(d=d, year=year, month=month)
                for d in dicts
            ]
        )

    def _day_dict_from_csv_to_day_record(self, d, year, month):
        day = date(year=year, month=month, day=int(d['day']))
        return DayRecord(
            day=day,
            day_type=d['day_type'],
            checkin=_parse_time(d['checkin'], day),
            checkout=_parse_time(d['checkout'], day),
        )


class Policy(object):
    u"""Calculate balance on periods."""

    def day_balance(self, day_record):
        raise NotImplementedError()

    def month_balance(self, month_record):
        return sum((self.day_balance(d) for d in month_record.records), timedelta(0))

    def year_balance(self, year_record):
        return sum((self.month_balance(m) for m in year_record.records), timedelta(0))

    def timesheet_balance(self, timesheet):
        return sum((self.year_balance(y) for y in timesheet.records), timedelta(0))


class HourPerDaysPolicy(Policy):

    def __init__(self, hours_per_day):
        self.hours_per_day = hours_per_day

    def day_balance(self, day_record):
        return (
            (day_record.worked() - timedelta(hours=self.hours_per_day))
            if (day_record.day_type == 'N')
            else timedelta(0)
        )


DEFAULT_POLICY = HourPerDaysPolicy(hours_per_day=7)


def report(db, policy, path):
    if os.path.exists(path):
        shutil.rmtree(path)
    mkdirp(path)

    with open(os.path.join(path, 'totals.txt'), 'w') as f:
        print >> f, 'Worked: {}'.format(timedelta_to_str(db.worked()))
        print >> f, 'Balance: {}'.format(timedelta_to_str(policy.timesheet_balance(db)))

    for year_record in db.records:
        year_path = os.path.join(path, str(year_record.year))
        mkdirp(year_path)

        with open(os.path.join(year_path, 'totals.txt'), 'w') as f:
            print >> f, 'Worked: {}'.format(timedelta_to_str(year_record.worked()))
            print >> f, 'Balance: {}'.format(timedelta_to_str(policy.year_balance(year_record)))

        for month_record in year_record.records:
            month_path = os.path.join(year_path, '{:02d}.txt'.format(month_record.month))

            with open(month_path, 'w') as f:
                print >> f, DAY_HEADER_TEMPLATE
                for day_record in month_record.records:
                    print >> f, day_record_to_report_line(day_record, policy)

                print >> f, 'Worked: {}'.format(timedelta_to_str(month_record.worked()))
                month_balance = timedelta_to_str(policy.month_balance(month_record))
                print >> f, 'Balance: {}'.format(month_balance)

    print timedelta_to_str(policy.timesheet_balance(db))


def day_record_to_report_line(day_record, policy):
    return DAY_LINE_TEMPLATE.format(
        day=day_record.day,
        day_type=day_record.day_type,
        checkin=date_to_time_str(day_record.checkin),
        checkout=date_to_time_str(day_record.checkout),
        worked=timedelta_to_str(day_record.worked()),
        balance=timedelta_to_str(policy.day_balance(day_record)),
    )


def timedelta_to_str(t):
    seconds = abs(t.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return '{:02d}:{:02d}'.format(int(hours), int(minutes))


def date_to_time_str(d):
    return d.strftime('%H:%M') if d else '-'


def main():
    arguments = docopt(__doc__)

    db_path = arguments['<db_path>']
    out_path = arguments['<out_path>']

    timesheet = TimeSheet()
    timesheet.load(db_path)
    timesheet.print_timesheet()
    print

    for e in timesheet.validate():
        print e
    print

    report(timesheet, DEFAULT_POLICY, out_path)


def format_csv_dict(d):
    return {k.strip(): v.strip() for (k, v) in d.iteritems()}


def parse_csv(path):
    with open(path, 'r') as f:
        return [format_csv_dict(i) for i in csv.DictReader(f)]


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
