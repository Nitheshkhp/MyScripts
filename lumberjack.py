"""
Script to handle scenarios when Vertica's logrotate goes kaput.
This script can truncate a massive log file, saving data after a given date.
This script can also process a singular log file into separate log files containing data
for their respective dates.

The script is called lumberjack.py, because it cuts the logs :D.
Author: nitheshkhp@gmail.com

*I take no responsibility if the script nukes your DB* Use with caution*

"""
import sys
import re

from datetime import datetime, timedelta


def get_delta_date(current_date, days_to_add, date_format):
    """
    Returns incremented date.

    :param current_date: The date you want to increment.
    :param days_to_add: Number of days to increment.
    :param date_format: date format i.e. yyyy-mm-dd, yyyy/mm/dd etc.
    :return: Incremented date
    """
    date = datetime.strptime(current_date, date_format)
    next_date = date + timedelta(days=days_to_add)

    return datetime.strftime(next_date, date_format)


def generate_filenames(log):
    """
    Parse the log files and generate dates and filenames based on logs for unique dates.

    :param log: Log file to extract dates from.
    :return: dictionary of dates and filenames.
    """
    dates = []
    filenames = {}
    new_log_pattern = r'\d{4}[-]\d{2}[-]\d{2}'
    for line in open(log):
        val = line[0:10]
        if re.match(new_log_pattern, val):
            dates.append(val)

    unique_dates = list(set(dates))
    for d in unique_dates:
        filenames[d] = 'vertica.log_' + d.replace('-', '_')

    return filenames


def truncate_log(log_to_process, new_log, start_here, stop_here=None):
    """
    Parse the log files, starts writing to new file based on date pattern supplied.
    The new log file will contain logs from the date supplied.

    Usage: lumberjack.py <vertica.log> <yyyy-mm-dd>

    :param log_to_process: Log file to truncate.
    :param new_log: log file where truncated log will be stored.
    :param start_here: start date of the new log file.
    :param stop_here: stop date of the new log file. If None then rest of the file will be copied into new file.
    """
    new_file_lines = []
    start = None
    for line in open(log_to_process):
        if re.match(r"{pattern}.*(INFO New log)$".format(pattern=start_here), line):
            start = True
        if stop_here and re.match(r"{pattern}.*(INFO New log)$".format(pattern=stop_here), line):
            start = False
        if start:
            new_file_lines.append(line)

    with open(new_log, "a") as fo:
        fo.writelines(new_file_lines)


def main(action, log, date=None):
    """
    Generate a new log file based on Vertica's New log file generation.

    :param action: 'truncate' to generate a new log containing only the logs we need.
    'separate_logs' to cut the log into individual date based logs.
    :param log: log file to process.
    :param date: date is optional parameter, and is to be used only when truncating a log.
    """

    if action == "truncate":
        truncated_log = "truncated_vertica.log"
        truncate_log(log, truncated_log, date)

    elif action == "separate_logs":
        filenames = generate_filenames(log)
        for datum, filename in filenames.items():
            start_here = datum
            next_date = get_delta_date(start_here, 1, "%Y-%m-%d")
            if next_date not in filenames.keys():
                stop_here = None
            else:
                stop_here = next_date

            print("Processing log file for date: {} till date: {} ".format(start_here, stop_here))
            truncate_log(log, filename, datum, stop_here)


# Main
if __name__ == "__main__":
    pattern = ""
    action = sys.argv[1]
    log_to_process = sys.argv[2]

    # Handle the parameters
    if len(sys.argv) < 3:
        print("Please provide correct options to the script")
        print("Usage 'lumberjack.py <truncate/separate_logs> <log to process> <yyyy-mm-dd>'")
    if len(sys.argv) > 3:
        pattern = sys.argv[3]

    # Cut them logs.
    if action == "truncate":
        main(action, log_to_process, pattern)
    elif action == "separate_logs":
        main(action, log_to_process)
    else:
        print("Incorrect option used for the script")
        print("Usage 'lumberjack.py <truncate/separate_logs> <log to process> [<yyyy-mm-dd>]'")
