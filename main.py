# coding=utf8
"""Process time sheets.

Usage:
  timesheet [options] <db_path> <out_path>

Options:
  -h, --help            Print this help text.
  -l, --lang=<lang>     Translate output to the given language. Examples: "pt-br", "pt-BR", "pt_BR".
"""
from docopt import docopt
from report import report
from policy import DEFAULT_POLICY
from db import parse_db
from translations import get_translations


def main():
    arguments = docopt(__doc__)
    print arguments

    db_path = arguments['<db_path>']
    out_path = arguments['<out_path>']

    timesheet = parse_db(db_path)
    print

    for e in timesheet.validate():
        print e
    print

    translations = get_translations(arguments['--lang'])
    report(timesheet, DEFAULT_POLICY, out_path, translations=translations)


if __name__ == '__main__':
    main()
