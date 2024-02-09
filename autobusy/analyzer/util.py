import pandas as pd
import numpy as np


def distance(lon1: float, lat1: float, lon2: float, lat2: float):
    r = 6373.0
    lon1 = np.radians(lon1)
    lat1 = np.radians(lat1)
    lon2 = np.radians(lon2)
    lat2 = np.radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return r * c


def speed(dist: float, time: float):
    return dist / time


def strip_low_speeds(df: pd.DataFrame, threshold: float):
    return df[df['Speed'] > threshold]


def inversions(perm1: list, perm2: list):
    inv = 0
    for i in range(len(perm1)):
        for j in range(len(perm2)):
            if i < j and perm1.index(perm2[i]) > perm1.index(perm2[j]):
                inv += 1
    return inv


def get_common_sublists(lst1: list, lst2: list) -> tuple[list, list]:
    common_set = set(lst1) & set(lst2)
    return (list(dict.fromkeys(filter(lambda x: x in common_set, lst1))),
            list(dict.fromkeys(filter(lambda x: x in common_set, lst2))))
