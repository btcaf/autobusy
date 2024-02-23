import pandas as pd

from autobusy.analyzer.parser import TimetableParser, LiveParser
import unittest.mock
import pytest


@pytest.mark.parametrize('route_lines, expectation', [
    (["""
    *TR  2
        irrelevant line
        *LW 2
            irrelevant data    r 000000 irrelevant data
            irrelevant data    r 111111 irrelevant data
        #LW
        irrelevant line
        *LW 2
            irrelevant data    r 111111 irrelevant data
            irrelevant data    r 000000 irrelevant data
        #LW
    #TR
    """.split('\n'), [['000000', '111111'], ['111111', '000000']]])
])
def test_parse_line_routes(route_lines, expectation):
    result = TimetableParser.parse_line_routes(route_lines)
    assert result == expectation


@pytest.mark.parametrize('route_lines, expectation', [
    (["""
    irrelevant data
        *RP 2
            000000 irrelevant data Y=...    X=... irrelevant data
                irrelevant data
                *OD 2
                    0.00 irrelevant data
                    1.00 irrelevant data
                #OD
                irrelevant data
            111111 irrelevant data Y=...    X=... irrelevant data
                irrelevant data
                *OD 2
                    2.00 irrelevant data
                    3.00 irrelevant data
                #OD
                irrelevant data
        #RP
    #TR
    """.split('\n'), {'000000': ['0:00', '1:00'], '111111': ['2:00', '3:00']}])
])
def test_parse_line_timetables(route_lines, expectation):
    result = TimetableParser.parse_line_timetables(route_lines)
    assert result == expectation


def test_timetable_parser_init():
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data='data\ndata')) as m:
        parser = TimetableParser('filename')
        m.assert_called_once_with('filename', 'r', encoding='Windows-1250')
        assert parser.file_lines == ['data\n', 'data']


@pytest.mark.parametrize('file_contents, expectation', [
    (["""
    irrelevant data
    000000 name0, irrelevant Y= 0    X= 0 irrelevant
    irrelevant data
    111111 name1, irrelevant Y= 1    X= 1 irrelevant
    irrelevant data
    222222 name2, irrelevant Y= 2    X= 2 irrelevant
    irrelevant data
    """, pd.DataFrame({
        'ID': ['000000', '111111', '222222'],
        'Name': ['name0', 'name1', 'name2'],
        'Lat': [0, 1, 2],
        'Lon': [0, 1, 2]
    })])
])
def test_parse_stop_info(file_contents, expectation):
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=file_contents)):
        parser = TimetableParser('filename')
        result = parser.parse_stop_info()
        result.reset_index(inplace=True)
        assert result.equals(expectation)


@pytest.mark.parametrize('file_contents, expectation', [
    (["""
    irrelevant data
    Linia: 1 irrelevant data
        *TR  2
            irrelevant line
            *LW 2
                irrelevant data    r 000000 irrelevant data
                irrelevant data    r 111111 irrelevant data
            #LW
            irrelevant line
            *RP 2
                000000 irrelevant data Y=...    X=... irrelevant data
                    irrelevant data
                    *OD 2
                        0.00 irrelevant data
                        1.00 irrelevant data
                    #OD
                    irrelevant data
                111111 irrelevant data Y=...    X=... irrelevant data
                    irrelevant data
                    *OD 2
                        2.00 irrelevant data
                        3.00 irrelevant data
                    #OD
                    irrelevant data
            *LW 2
                irrelevant data    r 111111 irrelevant data
                irrelevant data    r 000000 irrelevant data
            #LW
            irrelevant line
            *RP 2
                111111 irrelevant data Y=...    X=... irrelevant data
                    irrelevant data
                    *OD 2
                        4.00 irrelevant data
                        5.00 irrelevant data
                    #OD
                    irrelevant data
                000000 irrelevant data Y=...    X=... irrelevant data
                    irrelevant data
                    *OD 2
                        6.00 irrelevant data
                        7.00 irrelevant data
                    #OD
                    irrelevant data
        #TR
    irrelevant data
    """, ({
                    '1': [['000000', '111111'], ['111111', '000000']],
                },
          {
                    '1': {'000000': ['0:00', '1:00', '6:00', '7:00'], '111111': ['2:00', '3:00', '4:00', '5:00']}
                })
      ])
])
def test_parse_line_info(file_contents, expectation):
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=file_contents)):
        parser = TimetableParser('filename')
        result = parser.parse_line_info()
        assert result == expectation


def test_live_parser_init():
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data='{"test": "test"}')) as m:
        parser = LiveParser('filename')
        m.assert_called_once_with('filename', 'r')
        assert parser.results == {'test': 'test'}


@pytest.mark.parametrize('file_contents, expectation', [
    ("""
    [
        {
            "request_time": "2024-01-29 03:00:30",
            "result": [
                {
                    "Line": "1",
                    "VehicleNumber": "1",
                    "Brigade": "1",
                    "Lon": 1,
                    "Lat": 1,
                    "Time": "2024-01-29 03:00:10"
                },
                {
                    "Line": "1",
                    "VehicleNumber": "2",
                    "Brigade": "2",
                    "Lon": 2,
                    "Lat": 2,
                    "Time": "2024-01-29 03:00:20"
                }
            ]
        }
    ]
    """, pd.DataFrame({
        'Line': ['1', '1'],
        'VehicleNumber': ['1', '2'],
        'Brigade': ['1', '2'],
        'Lon': [1, 2],
        'Lat': [1, 2],
        'Time': ['2024-01-29 03:00:10', '2024-01-29 03:00:20'],
        'RequestTime': ['2024-01-29 03:00:30', '2024-01-29 03:00:30']
    }))
])
def test_live_parser_parse(file_contents, expectation):
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=file_contents)):
        parser = LiveParser('filename')
        result = parser.parse()
        expectation['Time'] = pd.to_datetime(expectation['Time'])
        expectation['RequestTime'] = pd.to_datetime(expectation['RequestTime'])
        assert result.equals(expectation)
