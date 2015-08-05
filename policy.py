# coding=utf8
from datetime import timedelta


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
        if day_record.day_type == 'NOR':
            return day_record.worked() - timedelta(hours=self.hours_per_day)

        if day_record.day_type == 'ABS':
            return -timedelta(hours=self.hours_per_day)

        return timedelta(0)


DEFAULT_POLICY = HourPerDaysPolicy(hours_per_day=7)
