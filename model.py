# coding=utf8
from datetime import date
from datetime import datetime
from datetime import timedelta
from util import date_to_time_str
from util import pairwise
from util import timedelta_to_str
import calendar


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

    valid_day_types = (
        'NOR',  # Normal.
        'WE',  # Weekend.
        'HOL',  # Holiday,
        'VAC',  # Vacation.
        'ABS',  # Absence.
        'COM',  # Day off due to compensation.
        'Z',  # Other.
    )

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

        if (self.day_type == 'NOR') and not (self.checkin and self.checkout):
            errors.append('Day type is "NOR" but no checkin or checkout.')

        if (self.day_type in ('VAC', 'Z', 'ABS')) and (self.checkin or self.checkout):
            errors.append('Day type cannot have checkin or checkout.')

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
        end_day = last_day_of_month
        today = date.today()
        if (self.year == today.year) and (self.month == today.month):
            end_day = today.day if (today.day == 1) else (today.day - 1)

        for r in self.records:
            if (r.day.year != self.year) or (r.day.month != self.month):
                errors.append('Record belongs to another month: {}'.format(r.identifier()))

        for i in xrange(start_day, end_day + 1):
            if not self.get_day_record(i):
                errors.append('Missing day: {}.'.format(i))

        sorted_records = sorted(self.records, key=lambda r: r.checkin or datetime.max)
        for (a, b) in pairwise(sorted_records):
            if (a.checkin and a.checkout and b.checkin) and (a.checkin <= b.checkin <= a.checkout):
                errors.append('Overlapping records: ({}) and ({})'.format(a, b))

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

    def validate(self):
        errors = CompositeRecord.validate(self)

        for r in self.records:
            if r.year != self.year:
                errors.append('Record belongs to another year: {}'.format(r.identifier()))

        return errors


class TimeSheet(CompositeRecord):

    def __init__(self, records=None, adjustments=None):
        self.records = records if (records is not None) else []
        self.adjustments = adjustments if (adjustments is not None) else []

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


class AdjustmentRecord(Record):
    u"""An amount of time to be added to (or removed from) a balance."""

    def __init__(self, day, delta):
        self.day = day
        self.delta = delta

    def worked(self):
        return self.delta

    def validate(self):
        return ()

    def identifier(self):
        return 'Adjustment of {} [{}]'.format(
            timedelta_to_str(self.delta),
            self.day.strftime('%Y-%m-%d')
        )
