import requests
import json
import time

URL = 'https://api.um.warszawa.pl/api/action/busestrams_get'
RESOURCE_ID = 'f2e5503e-927d-4ad3-9500-4ab9e55deb59'
TIMEOUT = 10
TYPE = 1


def check_list_of_hours(hours: list[int]):
    if len(hours) > 24:
        raise ValueError('List of hours is too long')
    if not all(0 <= x < 24 for x in hours):
        raise ValueError('List of hours must only contain integers between 0 and 23')
    if len(set(hours)) != len(hours):
        raise ValueError('List of hours must contain different integers')