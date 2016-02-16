# coding=utf8
from datetime import timedelta


class Policy(object):
    u"""Calculate balance on periods."""

    def day_balance(self, day_record):
        raise NotImplementedError()

    def month_balance(self, month_record):
        return self.composite_balance(month_record, self.day_balance)

    def year_balance(self, year_record):
        return self.composite_balance(year_record, self.month_balance)

    def timesheet_balance(self, timesheet):
        return (
            self.composite_balance(timesheet, self.year_balance) +
            sum((a.delta for a in timesheet.adjustments), timedelta(0))
        )

    def composite_balance(self, composite_record, balance_func):
        return sum((balance_func(r) for r in composite_record.records), timedelta(0))


class HourPerDaysPolicy(Policy):

    def __init__(self, hours_per_day):
        self.hours_per_day = hours_per_day

    def day_balance(self, day_record):
        if day_record.day_type == 'NOR':
            return day_record.worked() - timedelta(hours=self.hours_per_day)

        if day_record.day_type == 'ABS':
            return -timedelta(hours=self.hours_per_day)

        if day_record.day_type == 'WE':
            return day_record.worked()

        return timedelta(0)


DEFAULT_POLICY = HourPerDaysPolicy(hours_per_day=7)
