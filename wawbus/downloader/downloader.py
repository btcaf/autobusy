from util import add_to_json, get_current_data, check_list_of_hours
import argparse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

call_count = 0


def job(key, file):
    global call_count
    call_count += 1
    try:
        add_to_json(get_current_data(key), file)
        logging.info("Added new data to file")
    except Exception as e:
        logging.error('Exception occurred: %s', repr(e))


def main(args):
    check_list_of_hours(args.hours)

    scheduler = BackgroundScheduler()
    trigger = OrTrigger([
        CronTrigger(hour=str(hour), minute='*', second='30') for hour in args.hours
    ])
    scheduler.add_job(job, trigger, args=[args.key, args.file])

    scheduler.start()

    try:
        while call_count < len(args.hours) * 60:
            time.sleep(5)
    finally:
        scheduler.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--key',
        help='API key'
    )
    parser.add_argument(
        '--file',
        help='File to save data to'
    )
    parser.add_argument(
        '--hours',
        help='List of hours to gather data',
        nargs="+",
        type=int
    )
    program_args = parser.parse_args()
    main(program_args)
