from config_utils import read_config, recursive_dict_merge, _DEFAULT_CONFIG


def test_recursive_dict_merge():
    left = {"a": 1, "b": 2, "c": 3, "x": {}, "y": {"a": 1}, "z": {"a": 1, "b": 2}}
    right = {"a": 8, "c": "8", "x": {"a": 5}, "y": {"b": 3}, "z": {"b": 7, "c": 9}}
    expected = {
        "a": 8,
        "b": 2,
        "c": "8",
        "x": {"a": 5},
        "y": {"a": 1, "b": 3},
        "z": {"a": 1, "b": 7, "c": 9},
    }
    assert recursive_dict_merge(left, right) == expected


def test_default_config():
    assert read_config() == _DEFAULT_CONFIG
