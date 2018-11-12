import pylspclient
from pytest_mock import mocker 

# content of test_sample.py
def func(x):
    return x + 1

def test_answer():
    assert func(3) == 5
