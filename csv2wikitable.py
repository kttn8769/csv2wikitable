import sys
import argparse
import re
import csv
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(
        description='Convert csv table into MediaWiki table.'
    )
    parser.add_argument(
        '-i', '--input', type=str, required=True, help='Input csv file.'
    )
    parser.add_argument(
        '-o', '--output', type=str, required=False, default=None,
        help=('Output file. If not specified, the output will be printed to '
              'STDOUT')
    )
    args = parser.parse_args()
    return args


def read_csv(csvfile):
    try:
        csvdata = []
        with open(csvfile) as f:
            lines = f.readlines()
    except IOError:
        print('Failed to read input file.', file=sys.stderr)
        sys.exit(1)

    for line in csv.reader(lines):
        line = [x.strip() for x in line]
        csvdata.append(line)

    return csvdata


def split_title_and_table(elems):
    # Title
    n_values = np.sum(np.array(elems[0] != ''))
    assert n_values == 1, "Title row must have only one column."
    title_raw = elems[0][0]

    # Table
    for i in range(1, len(elems)):
        if i == 1:
            n_elems_prev = len(elems[i])
        else:
            n_elems = len(elems[i])
            assert n_elems == n_elems_prev, (
                "line {}: Numer of columns must be the same for all rows"
                " except title row.").format(i)
            n_elems_prev = n_elems
    table = np.array(elems[1:])

    return title_raw, table


def parse_title(title_raw):
    match_result = re.match(r'{(\d+)}(.+)', title_raw)
    if match_result is not None:
        table_width = int(match_result.group(1))
        title = match_result.group(2)
    else:
        table_width = None
        title = title_raw
    return title, table_width


def parse_table(table):
    table = np.copy(table)
    is_heading = np.zeros_like(table, dtype=bool)
    column_widths = np.zeros(table.shape[1], dtype=int)

    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            # Do nothing if empty
            if table[i, j] == '':
                continue

            # Check if heading cell
            if table[i, j][0] == '!':
                is_heading[i, j] = True
                if len(table[i, j]) > 1:
                    table[i, j] = table[i, j][1:]
                else:
                    table[i, j] == ''

            # Check if column width specified
            if i == 0:
                match_result = re.match(r'{(\d+)}(.+)', table[i, j])
                if match_result is not None:
                    column_widths[j], table[i, j] = match_result.groups()

    return table, is_heading, column_widths


def generate_source(table_width, title, table, is_heading, column_widths):
    out = ''

    # Set table width
    out += '{| class="wikitable"'
    if table_width > 0:
        out += ' style="width:{:d}%"\n'.format(table_width)
    else:
        out += '\n'

    # Set title
    out += '|+{:s}\n'.format(title)

    # Write table
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            if is_heading[i, j]:
                out += '!'
            else:
                out += '|'

            if i == 0:
                if column_widths[j] > 0:
                    out += ' style="width:{:d}%" |'.format(column_widths[j])

            out += ' {:s}\n'.format(table[i, j])

        if i != table.shape[0] - 1:
            out += '|-\n'
    out += '|}\n'

    return out


def main():
    args = parse_args()

    elems = read_csv(args.input)

    title_raw, table = split_title_and_table(elems)

    title, table_width = parse_title(title_raw)

    table, is_heading, column_widths = parse_table(table)

    output = generate_source(
        table_width, title, table, is_heading, column_widths)

    if args.output is None:
        print(output)
    else:
        try:
            with open(args.output, 'w') as f:
                f.write(output)
        except IOError:
            print('Failed to open output file.', file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
