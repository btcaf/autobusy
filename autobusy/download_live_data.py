from autobusy.downloader.downloader import RequestConfig, RequestHandler
import argparse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def check_list_of_hours(hours: list[int]):
    if len(hours) > 24:
        raise ValueError('List of hours is too long')
    if not all(0 <= x < 24 for x in hours):
        raise ValueError('List of hours must only contain integers between 0 and 23')
    if len(set(hours)) != len(hours):
        raise ValueError('List of hours must contain different integers')


call_count = 0


def job(request_handler: RequestHandler):
    global call_count
    call_count += 1
    try:
        request_handler.get_locations_to_json()
        logging.info("Added new data to file")
    except Exception as e:
        logging.error('Exception occurred: %s', repr(e))


def main(args):
    check_list_of_hours(args.hours)
    config = RequestConfig(args.key)
    request_handler = RequestHandler(config, args.file)

    scheduler = BackgroundScheduler()
    trigger = OrTrigger([
        CronTrigger(hour=str(hour), minute='*', second='30') for hour in args.hours
    ])
    scheduler.add_job(job, trigger, args=[request_handler])

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
        help='API key',
        required=True
    )
    parser.add_argument(
        '--file',
        help='File to save data to',
        required=True
    )
    parser.add_argument(
        '--hours',
        help='List of hours to gather data',
        required=True,
        nargs="+",
        type=int
    )
    program_args = parser.parse_args()
    main(program_args)
