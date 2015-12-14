# coding=utf8
"""Import data from timerec Android app.

Usage:
  timerec [options] <db_path> <csv_path>

Options:
  -h, --help          Print this help text.
"""
from docopt import docopt
from util import parse_csv
from model import DayRecord
from datetime import datetime
from util import parse_time
from db import write_day_record


def main():
    arguments = docopt(__doc__)

    db_path = arguments['<db_path>']
    csv_path = arguments['<csv_path>']

    dicts = parse_csv(csv_path)
    day_records_from_csv = (dict_to_day_record(d) for d in dicts)
    day_records_from_csv = [r for r in day_records_from_csv if r]

    for day_record_from_csv in day_records_from_csv:
        inserted = write_day_record(db_path, day_record_from_csv)
        if inserted:
            print 'Inserted {}'.format(day_record_from_csv)
        else:
            print 'Discarded: {}'.format(day_record_from_csv)


def dict_to_day_record(d):
    if d['Data'] == 'Total':
        return None

    day = datetime.strptime(d['Data'], '%Y/%m/%d').date()
    return DayRecord(
        day=day,
        day_type='NOR',
        checkin=parse_time(d['Check-In'], day),
        checkout=parse_time(d['Check-Out'], day),
    )


if __name__ == '__main__':
    main()
