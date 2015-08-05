# coding=utf8
from datetime import date
from model import DayRecord
from model import MonthRecord
from model import TimeSheet
from model import YearRecord
from util import parse_csv
from util import parse_time
from util import mkdirp
import os
import re


YEAR_DIR_PATTERN = re.compile(r'^\d\d\d\d$')
MONTH_FILE_PATTERN = re.compile(r'^\d\d\.csv$')


def parse_db(path):
    year_dirs = sorted(
        i for i in os.listdir(path)
        if YEAR_DIR_PATTERN.match(i) is not None
    )
    return TimeSheet(records=[
        parse_year(os.path.join(path, year_dir))
        for year_dir
        in year_dirs
    ])


def parse_year(year_path):
    year = int(os.path.basename(year_path))
    month_files = sorted(
        i for i in os.listdir(year_path)
        if MONTH_FILE_PATTERN.match(i) is not None
    )

    return YearRecord(
        year=year,
        records=[
            parse_month(os.path.join(year_path, month_file), year)
            for month_file in month_files
        ]
    )


def parse_month(month_path, year):
    month = int(os.path.basename(month_path).split('.')[0])
    dicts = parse_csv(month_path)
    return MonthRecord(
        year=year,
        month=month,
        records=[
            _day_dict_from_csv_to_day_record(d=d, year=year, month=month)
            for d in dicts
        ]
    )


def write_day_record(db_path, day_record):
    month_path = os.path.join(
        db_path,
        str(day_record.day.year),
        '{:02d}.csv'.format(day_record.day.month)
    )
    mkdirp(os.path.dirname(month_path))
    if not os.path.exists(month_path):
        with open(month_path, 'w') as f:
            f.write('day,day_type,checkin,checkout\n')

    month_record = parse_month(month_path, year=day_record.day.year)
    if month_record.get_day_record(day_record.day.day):
        return False

    with open(month_path, 'a') as f:
        f.write(
            ','.join([
                str(day_record.day.day),
                day_record.day_type,
                day_record.checkin.strftime('%H:%M'),
                day_record.checkout.strftime('%H:%M'),
            ]) + '\n'
        )

    return True


def _day_dict_from_csv_to_day_record(d, year, month):
    day = date(year=year, month=month, day=int(d['day']))
    return DayRecord(
        day=day,
        day_type=d['day_type'],
        checkin=parse_time(d['checkin'], day),
        checkout=parse_time(d['checkout'], day),
    )
