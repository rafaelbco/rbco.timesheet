# coding=utf8
from datetime import date
from datetime import timedelta
import calendar
import os
import re
from util import date_to_time_str
from util import timedelta_to_str
from util import parse_time
from util import parse_csv


YEAR_DIR_PATTERN = re.compile(r'^\d\d\d\d$')
MONTH_FILE_PATTERN = re.compile(r'^\d\d\.csv$')


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
            checkin=parse_time(d['checkin'], day),
            checkout=parse_time(d['checkout'], day),
        )