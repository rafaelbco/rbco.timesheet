# coding=utf8
"""Process time sheets.

Usage:
  timesheet [options] <db_path> <out_path>

Options:
  -h, --help          Print this help text.
"""
import os
import shutil
from util import mkdirp
from util import timedelta_to_str
from util import date_to_time_str

DAY_HEADER_TEMPLATE = '    '.join([
    '{:<3}'.format('day'),
    '{:<5}'.format('type'),
    '{:<5}'.format('in'),
    '{:<5}'.format('out'),
    '{:<10}'.format('worked'),
    '{:>8}'.format('balance'),

])
DAY_LINE_TEMPLATE = '    '.join([
    '{day:%d} ',
    '{day_type:<5}',
    '{checkin:<5}',
    '{checkout:<5}',
    '{worked:<10}',
    '{balance:>8}',
])


def report(db, policy, path):
    if os.path.exists(path):
        shutil.rmtree(path)
    mkdirp(path)

    with open(os.path.join(path, 'totals.txt'), 'w') as f:
        print >> f, 'Worked: {}'.format(timedelta_to_str(db.worked()))
        print >> f, 'Balance: {}'.format(timedelta_to_str(policy.timesheet_balance(db)))
        # if db.adjustments:
        #     print >> f, 'Adjustments:'
        #     for a in db.adjustments:
        #         print >> f, '    ' + a.identifier()

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

    print 'Balance: {}'.format(timedelta_to_str(policy.timesheet_balance(db)))


def day_record_to_report_line(day_record, policy):
    return DAY_LINE_TEMPLATE.format(
        day=day_record.day,
        day_type=day_record.day_type,
        checkin=date_to_time_str(day_record.checkin),
        checkout=date_to_time_str(day_record.checkout),
        worked=timedelta_to_str(day_record.worked()),
        balance=timedelta_to_str(policy.day_balance(day_record)),
    )
