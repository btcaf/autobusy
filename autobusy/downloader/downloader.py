import requests
import time
import ftplib
import json


class RequestConfig:
    def __init__(self, apikey: str):
        self.url = 'https://api.um.warszawa.pl/api/action/busestrams_get'
        self.resource_id = 'f2e5503e-927d-4ad3-9500-4ab9e55deb59'
        self.timeout = 10
        self.type = 1
        self.apikey = apikey


class RequestHandler:
    def __init__(self, config: RequestConfig, output_file: str):
        self.config = config
        self.output_file = output_file

    def get_bus_locations(self):
        params = {
            'resource_id': self.config.resource_id,
            'apikey': self.config.apikey,
            'type': self.config.type,
            'timeout': self.config.timeout
        }

        r = requests.post(self.config.url, params=params)
        r.raise_for_status()
        if not isinstance(r.json()["result"], list):
            raise TypeError(f'Invalid response: {r.json()["result"]}')
        return {
            "request_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "result": r.json()["result"],
        }

    def get_locations_to_json(self):
        data = self.get_bus_locations()
        try:
            with open(self.output_file, 'r+') as f:
                data = json.load(f)
                data.append(data)
                f.seek(0)
                f.write(json.dumps(data, indent=4))
        except FileNotFoundError:
            with open(self.output_file, 'w') as f:
                f.write(json.dumps([data], indent=4))


class FTPConfig:
    def __init__(self):
        self.host = 'rozklady.ztm.waw.pl'


class TimetableDataDownloader:
    def __init__(self, ftp_config: FTPConfig):
        self.ftp_config = ftp_config

    def list_timetables(self):
        with ftplib.FTP(self.ftp_config.host) as ftp:
            ftp.login()
            return ftp.nlst()

    def download_timetable(self, filename: str, local_filename: str):
        with ftplib.FTP(self.ftp_config.host) as ftp:
            ftp.login()
            with open(local_filename, 'wb') as f:
                ftp.retrbinary(f'RETR {filename}', f.write)
