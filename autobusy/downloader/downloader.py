import requests
import time
import ftplib
import json


class RequestConfig:
    """
    Configuration for the request to the API
    """
    def __init__(self, apikey: str):
        self.url = 'https://api.um.warszawa.pl/api/action/busestrams_get'
        self.resource_id = 'f2e5503e-927d-4ad3-9500-4ab9e55deb59'
        self.timeout = 10
        self.type = 1
        self.apikey = apikey


class RequestHandler:
    """
    Class for handling requests to the API
    """
    def __init__(self, config: RequestConfig, output_file: str):
        """
        Constructor
        :param config: Configuration for the request
        :param output_file: Name of the file to save the data to
        """
        self.config = config
        self.output_file = output_file

    def get_bus_locations(self) -> dict:
        """
        Get bus locations from the API
        :return: dict with request time and result field of response
        """
        params = {
            'resource_id': self.config.resource_id,
            'apikey': self.config.apikey,
            'type': self.config.type,
            'timeout': self.config.timeout
        }

        r = requests.post(self.config.url, params=params)
        r.raise_for_status()

        # sometimes the response has error information in the result field,
        # so we need to check if the result is a list
        if not isinstance(r.json()["result"], list):
            raise TypeError(f'Invalid response: {r.json()["result"]}')
        return {
            "request_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "result": r.json()["result"],
        }

    def get_locations_to_json(self):
        """
        Get bus locations and save them to a JSON file
        If the file already exists, append the data to it
        :return: None
        """
        data = self.get_bus_locations()
        try:
            with open(self.output_file, 'r+') as f:
                curr_data = json.load(f)
                curr_data.append(data)
                f.seek(0)
                f.write(json.dumps(curr_data, indent=4))
        except FileNotFoundError:
            with open(self.output_file, 'w') as f:
                f.write(json.dumps([data], indent=4))


class FTPConfig:
    """
    Configuration for the FTP server
    """
    def __init__(self):
        self.host = 'rozklady.ztm.waw.pl'


class TimetableDataDownloader:
    """
    Class for downloading timetable data from the FTP server
    """
    def __init__(self, ftp_config: FTPConfig):
        """
        Constructor
        :param ftp_config: Configuration for the FTP server
        """
        self.ftp_config = ftp_config

    def list_timetables(self):
        """
        List all files in the FTP server
        :return: list of filenames
        """
        with ftplib.FTP(self.ftp_config.host) as ftp:
            ftp.login()
            return ftp.nlst()

    def download_timetable(self, filename: str, local_filename: str):
        """
        Download a file with given name from the FTP server
        :param filename: Name of the file to download
        :param local_filename: Name of the file to save the data to
        :return: None
        """
        with ftplib.FTP(self.ftp_config.host) as ftp:
            ftp.login()
            with open(local_filename, 'wb') as f:
                ftp.retrbinary(f'RETR {filename}', f.write)
