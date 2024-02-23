import pytest
from autobusy.downloader.downloader import RequestHandler, RequestConfig
from requests import HTTPError
import inspect
from unittest import mock
import json
import pyfakefs


@pytest.fixture
def request_handler():
    config = RequestConfig('test_key')
    return RequestHandler(config, 'test_file.json')


mock_time = mock.Mock()
mock_time.return_value = '2021-01-01 00:00:00'


@pytest.mark.parametrize(
    "json_response,status,expectation",
    [
        ({
             'result': [
                 {
                     'Lines': '1',
                     'Lon': '21.011',
                     'VehicleNumber': '1234',
                     'Time': '2020-01-01 00:00:00',
                     'Lat': '52.123'
                 }
             ]
         },
         200,
         {
             'result': [
                 {
                     'Lines': '1',
                     'Lon': '21.011',
                     'VehicleNumber': '1234',
                     'Time': '2020-01-01 00:00:00',
                     'Lat': '52.123'
                 }
             ],
             'request_time': '2021-01-01 00:00:00'
         }),
        ({
             'result': 'Błędna metoda lub parametry wywołania'
         },
         200,
         TypeError),
        ({
             'result': [
                 {
                     'Lines': '1',
                     'Lon': '21.011',
                     'VehicleNumber': '1234',
                     'Time': '2020-01-01 00:00:00',
                     'Lat': '52.123'
                 }
             ]
         },
         500,
         HTTPError),
    ],
)
@mock.patch('time.strftime', mock_time)
def test_get_bus_locations(json_response, status, expectation, requests_mock, request_handler):
    url = 'https://api.um.warszawa.pl/api/action/busestrams_get'
    requests_mock.post(url, json=json_response, status_code=status)
    if inspect.isclass(expectation) and issubclass(expectation, Exception):
        with pytest.raises(expectation):
            request_handler.get_bus_locations()
    else:
        assert request_handler.get_bus_locations() == expectation


mock_get_bus_locations = mock.Mock()
mock_get_bus_locations.return_value = {
    "request_time": "2021-01-01 00:00:00",
    "result": [
        {
            "Lines": "1",
            "Lon": "21.011",
            "VehicleNumber": "1234",
            "Time": "2020-01-01 00:00:00",
            "Lat": "52.123"
        }
    ],
}


@mock.patch.object(RequestHandler, 'get_bus_locations', mock_get_bus_locations)
def test_get_locations_to_json(request_handler, fs):
    request_handler.get_locations_to_json()
    with open('test_file.json', 'r') as f:
        assert json.load(f) == [
            {
                "request_time": "2021-01-01 00:00:00",
                "result": [
                    {
                        "Lines": "1",
                        "Lon": "21.011",
                        "VehicleNumber": "1234",
                        "Time": "2020-01-01 00:00:00",
                        "Lat": "52.123"
                    }
                ]
            }
        ]
    request_handler.get_locations_to_json()
    with open('test_file.json', 'r') as f:
        assert json.load(f) == [
            {
                "request_time": "2021-01-01 00:00:00",
                "result": [
                    {
                        "Lines": "1",
                        "Lon": "21.011",
                        "VehicleNumber": "1234",
                        "Time": "2020-01-01 00:00:00",
                        "Lat": "52.123"
                    }
                ]
            },
            {
                "request_time": "2021-01-01 00:00:00",
                "result": [
                    {
                        "Lines": "1",
                        "Lon": "21.011",
                        "VehicleNumber": "1234",
                        "Time": "2020-01-01 00:00:00",
                        "Lat": "52.123"
                    }
                ]
            }
        ]
