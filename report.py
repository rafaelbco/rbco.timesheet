# coding=utf8
from util import date_to_time_str
from util import mkdirp
from util import timedelta_to_str
import os
import shutil
import sys

SEPARATOR = 4 * u' '
DAY_HEADER_TEMPLATE = SEPARATOR.join([
    u'{:<3}',
    u'{:<10}',
    u'{:<10}',
    u'{:<10}',
    u'{:<12}',
    u'{:>10}']
)
DAY_LINE_TEMPLATE = SEPARATOR.join([
    u'{day:%d} ',
    u'{day_type:<10}',
    u'{checkin:<10}',
    u'{checkout:<10}',
    u'{worked:<12}',
    u'{balance:>10}',
])


def report(db, policy, path, translations=None):

    if os.path.exists(path):
        shutil.rmtree(path)
    mkdirp(path)

    translations = translations or {}

    def translate(s):
        return translations.get(s, s)

    def println(f, template, *args, **kwargs):
        args = [translate(a) for a in args]
        kwargs = {k: translate(v) for (k, v) in kwargs.iteritems()}
        print >> f, template.format(*args, **kwargs).encode('utf8')

    with open(os.path.join(path, 'totals.txt'), 'w') as f:
        println(f, u'{}: {}', u'Worked', timedelta_to_str(db.worked()))
        println(f, u'{}: {}', u'Balance', timedelta_to_str(policy.timesheet_balance(db)))
        # if db.adjustments:
        #     print >> f, 'Adjustments:'
        #     for a in db.adjustments:
        #         print >> f, '    ' + a.identifier()

    for year_record in db.records:
        year_path = os.path.join(path, str(year_record.year))
        mkdirp(year_path)

        with open(os.path.join(year_path, 'totals.txt'), 'w') as f:
            println(f, u'{}: {}', u'Worked', timedelta_to_str(year_record.worked()))
            println(f, u'{}: {}', u'Balance', timedelta_to_str(policy.year_balance(year_record)))

        for month_record in year_record.records:
            month_path = os.path.join(year_path, '{:02d}.txt'.format(month_record.month))

            with open(month_path, 'w') as f:
                println(
                    f,
                    DAY_HEADER_TEMPLATE,
                    u'day',
                    u'type',
                    u'in',
                    u'out',
                    u'worked',
                    u'balance',
                )
                for day_record in month_record.records:
                    println(
                        f,
                        DAY_LINE_TEMPLATE,
                        day=day_record.day,
                        day_type=day_record.day_type,
                        checkin=date_to_time_str(day_record.checkin),
                        checkout=date_to_time_str(day_record.checkout),
                        worked=timedelta_to_str(day_record.worked()),
                        balance=timedelta_to_str(policy.day_balance(day_record)),
                    )

                println(f, u'{}: {}', u'Worked', timedelta_to_str(month_record.worked()))
                println(
                    f,
                    u'{}: {}',
                    u'Balance',
                    timedelta_to_str(policy.month_balance(month_record))
                )

    println(sys.stdout, u'{}: {}', u'Balance', timedelta_to_str(policy.timesheet_balance(db)))
