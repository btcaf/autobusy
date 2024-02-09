import pandas as pd
import json


class TimetableParser:
    def __init__(self, filename: str):
        with open(filename, 'r', encoding='Windows-1250') as f:
            self.file_lines = f.readlines()

    @staticmethod
    def parse_line_routes(route_lines: list[str]) -> list[list[str]]:
        res = []
        curr = []
        for route_line in route_lines:
            r_pos = route_line.find(' r ')
            if r_pos != -1:
                stop = route_line[r_pos:].split()[1]
                if stop != '-':
                    curr.append(stop)
            elif '#LW' in route_line:
                res.append(curr)
                curr = []
        return res

    @staticmethod
    def parse_line_timetables(route_lines: list[str]) -> dict[str, list[str]]:
        res = {}
        curr_stop = ''
        write = False
        for route_line in route_lines:
            if 'X=' in route_line:
                curr_stop = route_line.split()[0]
                res[curr_stop] = []
            elif '*OD' in route_line and curr_stop:
                write = True
            elif '#OD' in route_line:
                write = False
                curr_stop = ''
            elif write:
                hour = route_line.split()[0]
                hour_split = hour.split('.')
                res[curr_stop].append(str(int(hour_split[0]) % 24) + ':' + hour_split[1])
        return res

    def parse_stop_info(self) -> pd.DataFrame:
        stop_info = {}
        for file_line in self.file_lines:
            if 'X=' in file_line and 'Kier.' not in file_line:
                values = file_line.split()
                stop_info[values[0]] = {
                    'Name': ' '.join(values[1:-6]).strip(','),
                    'Lat': values[-4],
                    'Lon': values[-2]
                }

        stop_info_list = []
        for key in stop_info:
            dictionary = stop_info[key]
            dictionary['ID'] = key
            stop_info_list.append(dictionary)

        stop_info_df = pd.DataFrame(stop_info_list).set_index('ID')
        stop_info_df['Lat'] = pd.to_numeric(stop_info_df['Lat'], errors='coerce')
        stop_info_df['Lon'] = pd.to_numeric(stop_info_df['Lon'], errors='coerce')
        return stop_info_df

    def parse_line_info(self) -> tuple[dict[str, list[list[str]]], dict[str, dict[str, list[str]]]]:
        line_route_info = {}
        line_timetable_info = {}

        route_file_lines_dict = {}
        curr_bus_line = -1
        curr_route_file_lines = []
        for file_line in self.file_lines:
            if 'Linia' in file_line:
                curr_bus_line = file_line.split()[1]
            elif curr_bus_line != -1:
                if '#TR' in file_line:
                    route_file_lines_dict[curr_bus_line] = curr_route_file_lines
                    curr_route_file_lines = []
                    curr_bus_line = -1
                curr_route_file_lines.append(file_line)

        for bus_line in route_file_lines_dict:
            line_route_info[bus_line] = self.parse_line_routes(route_file_lines_dict[bus_line])
            line_timetable_info[bus_line] = self.parse_line_timetables(route_file_lines_dict[bus_line])

        return line_route_info, line_timetable_info

    def parse(self) -> tuple[pd.DataFrame, dict[str, list[list[str]]], dict[str, dict[str, list[str]]]]:
        stop_info = self.parse_stop_info()
        line_route_info, line_timetable_info = self.parse_line_info()
        return stop_info, line_route_info, line_timetable_info


class LiveParser:
    def __init__(self, filename: str):
        with open(filename, 'r') as f:
            self.results = json.load(f)

    def parse(self) -> pd.DataFrame:
        base_df = pd.concat([pd.DataFrame(x['result']) for x in self.results], ignore_index=True)
        base_df['Time'] = pd.to_datetime(base_df['Time'])
        request_time_df = pd.DataFrame([x['request_time'] for x in self.results for _ in range(len(x['result']))],
                                       columns=['RequestTime'])
        request_time_df['RequestTime'] = pd.to_datetime(request_time_df['RequestTime'])
        return pd.concat([base_df, request_time_df], axis=1)