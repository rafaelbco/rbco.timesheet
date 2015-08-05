# coding=utf8
"""Process time sheets.

Usage:
  timesheet [options] <db_path> <out_path>

Options:
  -h, --help          Print this help text.
"""
from docopt import docopt
from report import report
from policy import DEFAULT_POLICY
from db import parse_db


def main():
    arguments = docopt(__doc__)

    db_path = arguments['<db_path>']
    out_path = arguments['<out_path>']

    timesheet = parse_db(db_path)
    #timesheet.print_timesheet()
    print

    for e in timesheet.validate():
        print e
    print

    report(timesheet, DEFAULT_POLICY, out_path)


if __name__ == '__main__':
    main()
