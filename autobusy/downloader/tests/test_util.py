import pytest
from contextlib import nullcontext as does_not_raise
from requests import HTTPError
import inspect

from autobusy.downloader.util import add_to_json, get_current_data, check_list_of_hours


@pytest.mark.parametrize(
    "hours,expectation",
    [
        ([0], does_not_raise()),
        ([2, 1, 3, 7], does_not_raise()),
        (range(24), does_not_raise()),
        ([-1], pytest.raises(ValueError)),
        ([24], pytest.raises(ValueError)),
        (range(1000), pytest.raises(ValueError)),
        ([0, 0], pytest.raises(ValueError)),
        ([2, 3, 1, 2], pytest.raises(ValueError)),
    ],
)
def test_check_list_of_hours(hours: list, expectation):
    with expectation:
        check_list_of_hours(hours)


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
         [
             {
                 'Lines': '1',
                 'Lon': '21.011',
                 'VehicleNumber': '1234',
                 'Time': '2020-01-01 00:00:00',
                 'Lat': '52.123'
             }
         ]),
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
def test_get_current_data(json_response, status, expectation, requests_mock):
    url = 'https://api.um.warszawa.pl/api/action/busestrams_get'
    requests_mock.post(url, json=json_response, status_code=status)
    if inspect.isclass(expectation) and issubclass(expectation, Exception):
        with pytest.raises(expectation):
            get_current_data('test')
    else:
        assert get_current_data('test') == expectation
