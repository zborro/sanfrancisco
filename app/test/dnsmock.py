import pytest
from pytest import MonkeyPatch
import dns.asyncquery
from urllib.parse import urlparse


class FakeDnsAnswerEntry:
    def __init__(self, ip_list):
        self.ip_list = ip_list

    def to_rdataset(self):
        return self.ip_list


class FakeDnsAnswer:
    def __init__(self, ip_list):
        self.answer = FakeDnsAnswerEntry(ip_list)


class FakeDnsResponse:
    def __init__(self, ip_list):
        self.ip_list = ip_list

    def resolve_chaining(self):
        return FakeDnsAnswer(self.ip_list)


class DNSMock:
    def __init__(self):
        self._domains = {}
        self._exc = None

    def add_exception(self, exc):
        self._exc = exc

    def add_nameserver(self, ip, domains):
        def extract_host(url):
            return urlparse(url).netloc + "."

        self._domains[ip] = {extract_host(k): v for k, v in domains.items()}

    def resolve(self, nameserver, query):
        if self._exc:
            raise self._exc
        name = str(query.question[0].name)
        return self._domains[nameserver].get(name, [])


@pytest.fixture
def dns_mock(monkeypatch: MonkeyPatch) -> DNSMock:
    mock = DNSMock()

    async def fake_udp(query, nameserver, timeout):
        return FakeDnsResponse(mock.resolve(nameserver, query))

    monkeypatch.setattr(
        dns.asyncquery,
        "udp",
        fake_udp,
    )
    yield mock
