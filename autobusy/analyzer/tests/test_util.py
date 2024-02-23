import autobusy.analyzer.util as ut
import pandas as pd
import pytest


@pytest.mark.parametrize("lon1, lat1, lon2, lat2, expectation, tol", [
    (0, 0, 0, 0, 0, 0),
    (0, 0, 0, 1, 111, 0.5),
    (20.982075190290256, 52.21183403897336, 16.938678071885487, 52.40254719674715, 275.5, 0.5),
    (
        pd.Series([0, 0, 20.982075190290256]),
        pd.Series([0, 0,  52.21183403897336]),
        pd.Series([0, 0, 16.938678071885487]),
        pd.Series([0, 1, 52.40254719674715]),
        pd.Series([0, 111, 275.5]),
        0.5
    )
])
def test_distance(lon1, lat1, lon2, lat2, expectation, tol):
    if isinstance(lon1, pd.Series):
        assert (ut.distance(lon1, lat1, lon2, lat2) - expectation).abs().max() <= tol
    else:
        assert abs(ut.distance(lon1, lat1, lon2, lat2) - expectation) <= tol


@pytest.mark.parametrize("dist, time, expectation, tol", [
    (0, 1, 0, 0),
    (1, 1, 1, 0),
    (1, 2, 0.5, 0.5),
    (2, 1, 2, 0),
    (2, 2, 1, 0),
    (2, 3, 0.6666666666666666, 0.5),
    (3, 2, 1.5, 0),
    (3, 3, 1, 0),
    (3, 4, 0.75, 0.5),
    (
        pd.Series([0, 1, 1, 2, 2, 2, 3, 3, 3]),
        pd.Series([1, 1, 2, 1, 2, 3, 2, 3, 4]),
        pd.Series([0, 1, 0.5, 2, 1, 0.6666666666666666, 1.5, 1, 0.75]),
        0.5
    )
])
def test_speed(dist, time, expectation, tol):
    if isinstance(dist, pd.Series):
        assert (ut.speed(dist, time) - expectation).abs().max() <= tol
    else:
        assert abs(ut.speed(dist, time) - expectation) <= tol


@pytest.mark.parametrize("lst1, lst2, expectation", [
    ([], [], 0),
    ([1], [1], 0),
    ([1, 2], [1, 2], 0),
    ([2, 1], [1, 2], 1),
    ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1], 10),
    ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], 0),
    ([1, 2, 3, 4, 5], [2, 1, 3, 5, 4], 2),
    ([1, 2, 3, 4, 5], [1, 3, 2, 4, 5], 1),
    ([1, 2, 3, 4, 5], [1, 2, 4, 3, 5], 1),
    ([1, 2, 3, 4, 5], [1, 2, 3, 5, 4], 1),
    ([2, 3, 1, 4, 5], [3, 2, 1, 5, 4], 2),
])
def test_inversions(lst1, lst2, expectation):
    assert ut.inversions(lst1, lst2) == expectation


@pytest.mark.parametrize("lst1, lst2, expectation", [
    ([], [], ([], [])),
    ([1], [1], ([1], [1])),
    ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1], ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])),
    ([1, 2, 12, 4, 5], [5, 4, -3, 2, 1], ([1, 2, 4, 5], [5, 4, 2, 1])),
    ([3, 10], [9, 1], ([], []))
])
def test_get_common_sublists(lst1, lst2, expectation):
    assert ut.get_common_sublists(lst1, lst2) == expectation
