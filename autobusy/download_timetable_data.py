from autobusy.downloader.downloader import TimetableDataDownloader, FTPConfig
import argparse


def main(args):
    ftp_config = FTPConfig()
    downloader = TimetableDataDownloader(ftp_config)
    timetables = downloader.list_timetables()
    for timetable in timetables:
        print(timetable)
    print("Name file to download: ")
    filename = input()
    downloader.download_timetable(filename, args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output-file',
        help='Name of output file',
        required=True
    )
    program_args = parser.parse_args()
    main(program_args)
