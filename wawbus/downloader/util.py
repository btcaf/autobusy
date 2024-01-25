import requests
import json

URL = 'https://api.um.warszawa.pl/api/action/busestrams_get'
RESOURCE_ID = 'f2e5503e-927d-4ad3-9500-4ab9e55deb59'
TIMEOUT = 10
TYPE = 1


def check_list_of_hours(hours: list):
    if len(hours) > 24:
        raise ValueError('List of hours is too long')
    if not all(0 <= x < 24 for x in hours):
        raise ValueError('List of hours must only contain integers between 0 and 23')
    if len(set(hours)) != len(hours):
        raise ValueError('List of hours must contain different integers')


def get_current_data(apikey: str):
    r = requests.post(URL, params={
        'resource_id': RESOURCE_ID,
        'apikey': apikey,
        'type': TYPE,
        'timeout': TIMEOUT
    })
    r.raise_for_status()
    if not isinstance(r.json()['result'], list):
        raise TypeError(f'Invalid response: {r.json()["result"]}')
    return r.json()['result']


def add_to_json(data_list: list, filename: str):
    try:
        with open(filename, 'r+') as f:
            data = json.load(f)
            data.append(data_list)
            f.seek(0)
            f.write(json.dumps(data, indent=4))
    except FileNotFoundError:
        with open(filename, 'w') as f:
            f.write(json.dumps([data_list], indent=4))
