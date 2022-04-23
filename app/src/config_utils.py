import yaml
import os

_DEFAULT_CONFIG = {
    "net": {
        "dns_nameservers": ["1.1.1.1"],
        "dns_resolution_timeout_seconds": 5.0,
        "forbidden_networks": [
            "192.168.0.0/16",
            "10.0.0.0/8",
            "172.17.0.0/16",
            "127.0.0.0/8",
        ],
    },
    "http": {
        "ua_string": "cisco-bot/1337",
        "max_payload_size_bytes": 1024**2,
        # Protection against too many redirects (or redirection loops).
        # Set according to following example.
        # http://shorturl.com -> http://www.shorturl.com -> http://example.com -> http://www.example.com
        "max_redirects": 3,
        "timeout_connect_seconds": 5.0,
        "timeout_read_seconds": 5.0,
        "allow_binary_mime_types": False,
    },
}


def recursive_dict_merge(left, right):
    left = left.copy()

    for k, v in right.items():
        if k not in left or not isinstance(left[k], dict):
            left[k] = right[k]
        else:
            left[k] = recursive_dict_merge(left[k], right[k])

    return left


def read_config():
    try:
        with open(os.getenv("CONFIG_PATH", "config.yml")) as f:
            return recursive_dict_merge(_DEFAULT_CONFIG, yaml.safe_load(f))
    except FileNotFoundError:
        return _DEFAULT_CONFIG
