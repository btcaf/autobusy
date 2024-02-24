from autobusy.analyzer.analyzer import Analyzer, Results
import pytest


@pytest.mark.parametrize("routes, expectation", [
    ({
         '1': [['1', '2', '3'], ['3', '2', '1']],
     }, {
         '1': [['1', '2', '3'], ['3', '2', '1']],
     }),
    ({
         '1': [['1', '2', '3', '4'], ['1', '3', '4'], ['3', '2', '1'], ['2', '1']],
     }, {
         '1': [['1', '2', '3', '4'], ['3', '2', '1']],
     }),
    ({
         '1': [['1', '2', '3', '4'], ['1', '3', '4'], ['3', '2', '1'], ['2', '1']],
         '2': [['1', '2', '3', '4'], ['1', '3', '4']],
     }, {
         '1': [['1', '2', '3', '4'], ['3', '2', '1']],
         '2': [['1', '2', '3', '4']],
     }),
])
def test_get_max_opposite_routes(routes, expectation):
    assert Analyzer.get_max_opposite_routes(routes) == expectation
