import numpy as np


def distance(lon1, lat1, lon2, lat2):
    """
    Calculate distance between two points on Earth. Also works for dataframe parameters.
    :param lon1: Longitude of the first point
    :param lat1: Latitude of the first point
    :param lon2: Longitude of the second point
    :param lat2: Latitude of the second point
    :return: Distance in km
    """
    r = 6373.0  # Earth radius in km
    lon1 = np.radians(lon1)
    lat1 = np.radians(lat1)
    lon2 = np.radians(lon2)
    lat2 = np.radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return r * c


def speed(dist, time):
    """
    Calculate speed from distance and time. Also works for dataframe parameters.
    Does not check if time is zero
    :param dist: distance in km
    :param time: time in hours
    :return: speed in km/h
    """
    return dist / time


def inversions(perm1: list, perm2: list) -> int:
    """
    Calculate the number of inversions between two permutations of a set
    Does not check if the permutations are valid
    :param perm1: first permutation
    :param perm2: second permutation
    :return: number of inversions
    """
    inv = 0
    for i in range(len(perm1)):
        for j in range(len(perm2)):
            if i < j and perm1.index(perm2[i]) > perm1.index(perm2[j]):
                inv += 1
    return inv


def get_common_sublists(lst1: list, lst2: list) -> tuple[list, list]:
    """
    Get maximal sublists of two lists that only contain common elements of both lists
    :param lst1: first list
    :param lst2: second list
    :return: tuple of the two maximal sublists
    """
    common_set = set(lst1) & set(lst2)
    return (list(dict.fromkeys(filter(lambda x: x in common_set, lst1))),
            list(dict.fromkeys(filter(lambda x: x in common_set, lst2))))
