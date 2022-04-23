from host_resolver import HostResolver, DnsResolutionFailed, ForbiddenIpError
import pytest
from dnsmock import dns_mock
import dns.exception
from config_utils import _DEFAULT_CONFIG

test_config = _DEFAULT_CONFIG["net"]
host_resolver = HostResolver(test_config)


async def test_resolve_host(dns_mock):
    url = "http://doma.in/test"
    expected_ip_list = {"123.45.67.89"}
    dns_mock.add_nameserver("1.1.1.1", {url: expected_ip_list})

    ip_list = await host_resolver.resolve_host(url)
    assert ip_list == expected_ip_list


async def test_resolve_host_no_ips(dns_mock):
    dns_mock.add_nameserver("1.1.1.1", {})
    with pytest.raises(DnsResolutionFailed):
        await host_resolver.resolve_host("http://what.ever")


async def test_resolve_ip_address():
    ip = "4.3.2.1"
    assert await host_resolver.resolve_host(f"http://{ip}/resource") == {ip}


async def test_resolution_timeout(dns_mock):
    dns_mock.add_exception(dns.exception.Timeout)

    with pytest.raises(DnsResolutionFailed):
        await host_resolver.resolve_host("http://what.ever")

async def test_validate_ip_list():
    host_resolver.validate_ip_list(["12.34.56.78", "30.40.50.60"])
    with pytest.raises(ForbiddenIpError):
        host_resolver.validate_ip_list(["1.2.3.4", "10.30.40.50"])
