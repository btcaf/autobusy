import pandas as pd
import numpy as np
import autobusy.analyzer.util as util
import plotly.graph_objects as go
import folium
from datetime import datetime


class RouteData:
    def __init__(self, stop_info: pd.DataFrame, line_route_info: dict[str, list[list[str]]],
                 line_timetable_info: dict[str, dict[str, list[str]]]):
        self.stop_info = stop_info
        self.line_route_info = line_route_info
        self.line_timetable_info = line_timetable_info


class Analyzer:
    def __init__(self, hour: int):
        self.hour = hour
        self.results = Results()

    def create_speed_data(self, live_bus_df: pd.DataFrame):
        if self.results.speed_data is not None:
            return
        gk = live_bus_df[live_bus_df['Time'].dt.hour == self.hour].sort_values('Time').groupby('VehicleNumber')
        self.results.speed_data = gk.apply(
            lambda x: pd.concat([x['Lon'], x['Lat'], x['Time'], util.speed(
                util.distance(
                    x['Lon'].shift(),
                    x['Lat'].shift(),
                    x['Lon'],
                    x['Lat']
                ),
                (x['Time'] - x['Time'].shift()).dt.total_seconds() / 3600
            ).rename("Speed")], axis=1)
        ).dropna().reset_index(drop=True)

    def create_places_speed_data(self, live_bus_df: pd.DataFrame):
        if self.results.places_speed_data is not None:
            return
        if self.results.speed_data is None:
            self.create_speed_data(live_bus_df)
        speed_data = self.results.speed_data
        rounded_data = speed_data.round({'Lon': 2, 'Lat': 2})
        gk = rounded_data.groupby(['Lon', 'Lat'])
        self.results.places_speed_data = gk.apply(
            lambda x: pd.Series(
                [x.shape[0], x[x['Speed'] > 50].shape[0]],
                index=['Total', 'Fast']
            )
        ).reset_index()

    @staticmethod
    def get_max_opposite_routes(line_route_info: dict[str, list[list[str]]]):
        res = {}
        for line in line_route_info:
            max_route = max(line_route_info[line], key=len)
            reversed_routes = []
            for route in line_route_info[line]:
                route_groups = [stop[:4] for stop in route]
                max_route_groups = [stop[:4] for stop in max_route]
                max_route_groups.reverse()
                route_groups, max_route_groups = util.get_common_sublists(route_groups, max_route_groups)

                inversions = util.inversions(route_groups, max_route_groups)
                if inversions < len(route_groups) * (len(route_groups) - 1) / 4:
                    reversed_routes.append(route)

            if not reversed_routes:
                res[line] = [max_route]
            else:
                res[line] = [max_route, max(reversed_routes, key=len)]
        return res

    def initial_filter(self, live_bus_df: pd.DataFrame, route_data: RouteData):
        def filter_distance(df):
            for index1, row1 in df.iterrows():
                for index2, row2 in df.iterrows():
                    if index1 != index2:
                        if util.distance(row1['Lon'], row1['Lat'], row2['Lon'], row2['Lat']) > 1:
                            return True
            return False

        live_bus_df = live_bus_df.drop(live_bus_df[~live_bus_df["Lines"].isin(route_data.line_route_info)].index)
        live_bus_df = live_bus_df.drop(live_bus_df[live_bus_df["Time"].dt.hour != self.hour].index)
        return live_bus_df.groupby(['Lines', 'VehicleNumber']).filter(filter_distance)

    @staticmethod
    def add_closest_stops(live_bus_df: pd.DataFrame, route_data: RouteData):
        gk = live_bus_df.sort_values('Time').groupby(['Lines', 'VehicleNumber'])
        for name, group in gk:
            max_route = route_data.line_route_info[name[0]][0]
            for index, row in group.iterrows():
                dist_arr = np.array(
                    [
                        util.distance(
                            row['Lon'],
                            row['Lat'],
                            route_data.stop_info.loc[stop, 'Lon'],
                            route_data.stop_info.loc[stop, 'Lat']
                        )
                        for stop in max_route
                    ]
                )
                min_dist = np.min(dist_arr)
                id_min_dist = np.argmin(dist_arr)
                live_bus_df.loc[index, 'Closest'] = id_min_dist
                live_bus_df.loc[index, 'Distance'] = min_dist

    @staticmethod
    def filter_stationary_buses(live_bus_df: pd.DataFrame):
        live_bus_df = live_bus_df.drop(live_bus_df[live_bus_df['Distance'] > 1].index)
        return live_bus_df.groupby(['Lines', 'VehicleNumber']).filter(lambda x: x['Closest'].nunique() > 2)

    @staticmethod
    def get_types(lst: np.array):
        left_min_idx = np.where(lst == np.min(lst))[0][0]
        right_min_idx = np.where(lst == np.min(lst))[0][-1]
        left_max_idx = np.where(lst == np.max(lst))[0][0]
        right_max_idx = np.where(lst == np.max(lst))[0][-1]

        middle_min = (left_min_idx >= 3 and right_min_idx <= len(lst) - 4)
        middle_max = (left_max_idx >= 3 and right_max_idx <= len(lst) - 4)

        if middle_min and middle_max:
            return [-1] * len(lst)

        if middle_min:
            if np.max(lst[left_min_idx:right_min_idx + 1], initial=-1) == np.max(lst):
                return [-1] * len(lst)
            return [1 if i <= left_min_idx else 0 if i >= right_min_idx else -1 for i in range(len(lst))]

        if middle_max:
            if np.min(lst[left_max_idx:right_max_idx + 1], initial=-1) == np.min(lst):
                return [-1] * len(lst)
            return [0 if i <= left_max_idx else 1 if i >= right_max_idx else -1 for i in range(len(lst))]

        if left_min_idx < 3:
            return [0 if right_min_idx <= i <= left_max_idx else -1 for i in range(len(lst))]
        return [1 if right_max_idx <= i <= left_min_idx else -1 for i in range(len(lst))]

    @staticmethod
    def add_directions(live_bus_df: pd.DataFrame):
        gk = live_bus_df.sort_values('Time').groupby(['Lines', 'VehicleNumber'])
        live_bus_df['Direction'] = gk['Closest'].transform(lambda x: Analyzer.get_types(x.values))
        live_bus_df.drop(live_bus_df[live_bus_df['Direction'] == -1].index, inplace=True)
        live_bus_df.reset_index(drop=True, inplace=True)

    @staticmethod
    def min_dist_and_time(group: pd.DataFrame, stop: str, route_data: RouteData) -> tuple[float, str]:
        min_dist = np.inf
        min_time = None
        for _, row in group.iterrows():
            dist = util.distance(
                row['Lon'],
                row['Lat'],
                route_data.stop_info.loc[stop, 'Lon'],
                route_data.stop_info.loc[stop, 'Lat']
            )
            if dist < min_dist:
                min_dist = dist
                min_time = row['Time'].round('min').strftime('%H:%M')
        return min_dist, min_time

    @staticmethod
    def stop_arrival_info(live_bus_df: pd.DataFrame, route_data: RouteData) -> dict[str, dict[str, list[str]]]:
        stop_arrival_info = {}
        for line in live_bus_df['Lines'].unique():
            stop_arrival_info[line] = {}
            stops = set(route_data.line_route_info[line][0])
            if len(route_data.line_route_info[line]) > 1:
                stops = stops | set(route_data.line_route_info[line][1])
            for stop in stops:
                for i in range(0, len(route_data.line_route_info[line])):
                    if stop in route_data.line_route_info[line][i]:
                        cut_data = live_bus_df[(live_bus_df['Lines'] == line) & (live_bus_df['Direction'] == i)]
                        gk = cut_data.sort_values('Time').groupby('VehicleNumber')
                        for _, group in gk:
                            min_dist, min_time = Analyzer.min_dist_and_time(group, stop, route_data)
                            if min_dist < 1:
                                if stop in stop_arrival_info[line]:
                                    stop_arrival_info[line][stop].append(min_time)
                                else:
                                    stop_arrival_info[line][stop] = [min_time]
        return stop_arrival_info

    def get_differences(self, stop_arrival_info: dict[str, dict[str, list[str]]],
                        route_data: RouteData) -> tuple[list[pd.Series], int]:
        differences = []
        boundary_bus_count = 0

        for line in stop_arrival_info:
            for stop in route_data.line_timetable_info[line]:
                for departure_time in route_data.line_timetable_info[line][stop]:
                    datetime_object = datetime.strptime(departure_time, '%H:%M')
                    if datetime_object.hour != self.hour:
                        continue
                    if stop not in stop_arrival_info[line]:
                        boundary_bus_count += 1
                        continue
                    closest_time = min(
                        stop_arrival_info[line][stop],
                        key=lambda x: np.abs(datetime.strptime(x, '%H:%M') - datetime_object)
                    )
                    difference = (datetime.strptime(closest_time, '%H:%M') - datetime_object).total_seconds() // 60
                    if abs(difference) > datetime_object.minute or abs(difference) > 60 - datetime_object.minute:
                        boundary_bus_count += 1
                        continue
                    differences.append(pd.Series({
                        'Line': line,
                        'Stop': stop,
                        'Departure': departure_time,
                        'Closest': closest_time,
                        'Difference': abs(difference),
                        'Comment': 'Early' if difference < 0 else 'Late' if difference > 0 else 'On time'
                    }))
        return differences, boundary_bus_count

    def create_punctuality_data(self, live_bus_df: pd.DataFrame, route_data: RouteData):
        if self.results.punctuality_data is not None:
            return
        new_line_route_info = self.get_max_opposite_routes(route_data.line_route_info)
        route_data = RouteData(route_data.stop_info, new_line_route_info, route_data.line_timetable_info)
        live_bus_df = self.initial_filter(live_bus_df, route_data)
        self.add_closest_stops(live_bus_df, route_data)
        live_bus_df = self.filter_stationary_buses(live_bus_df)
        self.add_directions(live_bus_df)
        stop_arrival_info = self.stop_arrival_info(live_bus_df, route_data)
        differences, boundary_bus_count = self.get_differences(stop_arrival_info, route_data)
        self.results.punctuality_data = pd.DataFrame(differences)
        self.results.boundary_inaccuracy_count = boundary_bus_count

    def create_stop_punctuality_data(self, live_bus_df: pd.DataFrame, route_data: RouteData, tol: int):
        if self.results.punctuality_data is None:
            self.create_punctuality_data(live_bus_df, route_data)

        gk = self.results.punctuality_data.groupby('Stop')
        self.results.stop_punctuality_data = gk.apply(
            lambda x: pd.Series([x.shape[0], x[(x['Difference'] > tol) & (x['Comment'] == 'Late')].shape[0]],
                                index=['Total', 'Late'])).reset_index()
        self.results.stop_info = route_data.stop_info


class Results:
    def __init__(self):
        self.speed_data = None
        self.places_speed_data = None
        self.punctuality_data = None
        self.boundary_inaccuracy_count = None
        self.stop_punctuality_data = None
        self.stop_info = None

    def plot_speeds(self, delimiters: list[int]) -> go.Figure:
        if self.speed_data is None:
            raise ValueError('Speed data not created')
        speed_data = self.speed_data
        categories = [f'{delimiters[i]}-{delimiters[i + 1]}' for i in range(len(delimiters) - 1)]
        categories.append(f'{delimiters[-1]}+')
        values = [
            speed_data[(speed_data['Speed'] >= delimiters[i]) & (speed_data['Speed'] < delimiters[i + 1])].shape[0]
            for i in range(len(delimiters) - 1)
        ]
        values.append(speed_data[(speed_data['Speed'] >= delimiters[-1])].shape[0])
        fig = go.Figure(data=[go.Bar(x=categories, y=values)])
        fig.update_layout(
            title='Prędkości autobusów',
            title_x=0.5,
            xaxis_title='Prędkość [km/h]',
            yaxis_title='Liczba zarejestrowanch przypadków prędkości',
        )
        return fig

    def plot_fast_places(self, min_buses: int, min_ratio: float) -> folium.Map:
        if self.places_speed_data is None:
            raise ValueError('Places speed data not created')
        places_speed_data = self.places_speed_data
        fast_places = places_speed_data[(places_speed_data['Total'] > min_buses) &
                                        (places_speed_data['Fast'] / places_speed_data['Total'] > min_ratio)]
        m = folium.Map(location=[52.22977, 21.01178], zoom_start=11)
        for _, row in fast_places.iterrows():
            coordinates = [
                [row['Lat'] - 0.005, row['Lon'] - 0.005],
                [row['Lat'] + 0.005, row['Lon'] - 0.005],
                [row['Lat'] + 0.005, row['Lon'] + 0.005],
                [row['Lat'] - 0.005, row['Lon'] + 0.005],
                [row['Lat'] - 0.005, row['Lon'] - 0.005]
            ]
            folium.PolyLine(coordinates, color="red", weight=2.5,
                            tooltip=f"Liczba autobusów: {row['Total']}<br>"
                                    f"Liczba szybkich (powyżej 50 km/h): {row['Fast']}").add_to(
                m)

        return m

    def get_boundary_inaccuracy_percentage(self) -> float:
        if self.punctuality_data is None:
            raise ValueError('Punctuality data not created')
        if self.boundary_inaccuracy_count is None:
            raise ValueError('Boundary inaccuracy count not created')
        return (self.boundary_inaccuracy_count /
                (self.punctuality_data.shape[0] + self.boundary_inaccuracy_count) * 100)

    def plot_punctuality(self, delimiters: list[int]) -> go.Figure:
        if self.punctuality_data is None:
            raise ValueError('Punctuality data not created')

        categories = [f'>{delimiters[-1]} minut za wcześnie']
        categories += [
            f'{delimiters[i]}-{delimiters[i + 1]} minut za wcześnie'
            for i in reversed(range(len(delimiters) - 1))
        ]
        categories += [f'W obrębie {delimiters[0]} minut']
        categories += [
            f'{delimiters[i]}-{delimiters[i + 1]} minut za późno'
            for i in range(len(delimiters) - 1)
        ]
        categories += [f'>{delimiters[-1]} minut za późno']

        early_df = self.punctuality_data[self.punctuality_data['Comment'] == 'Early']
        on_time_df = self.punctuality_data[self.punctuality_data['Comment'] == 'On time']
        late_df = self.punctuality_data[self.punctuality_data['Comment'] == 'Late']

        values = [
            early_df[early_df['Difference'] > delimiters[-1]].shape[0]
        ]
        values += [
            early_df[(early_df['Difference'] >= delimiters[i]) & (early_df['Difference'] < delimiters[i + 1])].shape[0]
            for i in reversed(range(len(delimiters) - 1))
        ]
        values += [
            early_df[early_df['Difference'] < delimiters[0]].shape[0] +
            on_time_df.shape[0] +
            late_df[late_df['Difference'] > delimiters[0]].shape[0]
        ]
        values += [
            late_df[(late_df['Difference'] >= delimiters[i]) & (late_df['Difference'] < delimiters[i + 1])].shape[0]
            for i in range(len(delimiters) - 1)
        ]
        values += [
            late_df[late_df['Difference'] > delimiters[-1]].shape[0]
        ]

        fig = go.Figure(data=[go.Bar(x=categories, y=values)])
        fig.update_layout(
            title='Punktualność autobusów',
            title_x=0.5,
            xaxis_title='Różnica w minutach',
            yaxis_title='Liczba zarejestrowanch przypadków',
        )
        return fig

    def plot_bad_stops(self, min_buses: int, min_ratio: float) -> folium.Map:
        if self.stop_punctuality_data is None:
            raise ValueError('Stop punctuality data not created')
        stop_punctuality_data = self.stop_punctuality_data
        bad_stops = stop_punctuality_data[(stop_punctuality_data['Late'] / stop_punctuality_data['Total'] > min_ratio) &
                                          (stop_punctuality_data['Total'] > min_buses)]

        m = folium.Map(location=[52.22977, 21.01178], zoom_start=11)
        for _, row in bad_stops.join(self.stop_info, on='Stop').iterrows():
            folium.Marker(
                location=[row['Lat'], row['Lon']],
                popup=f"{row['Name']}<br>Liczba autobusów: {row['Total']}<br>Liczba spóźnionych: {row['Late']}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

        return m
