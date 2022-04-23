import ipaddress
import logging
import dns.message
import dns.asyncquery
import dns.asyncresolver
import dns.exception
from urllib.parse import urlparse


class DnsResolutionFailed(Exception):
    reason = 'dns resolution failed'


class ForbiddenIpError(Exception):
    reason = 'forbidden target host'


class HostResolver:
    def __init__(self, config):
        self.config = config

    async def resolve_host(self, url):
        host = urlparse(str(url)).netloc
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            return {host}

        async def resolve_using(nameserver, host):
            try:
                response = await dns.asyncquery.udp(
                    dns.message.make_query(host, "A"),
                    nameserver,
                    timeout=self.config["dns_resolution_timeout_seconds"],
                )
            except dns.exception.Timeout:
                logging.warning(
                    "DNS Lookup timed out for NS {} and host {}!".format(nameserver, host)
                )
                return []
            answer = response.resolve_chaining().answer
            return list(map(str, answer.to_rdataset())) if answer is not None else []

        ip_list = set(
            sum(
                [
                    await x
                    for x in map(lambda ns: resolve_using(ns, host), self.config["dns_nameservers"])
                ],
                [],
            )
        )
        if not ip_list:
            raise DnsResolutionFailed
        return ip_list

    def validate_ip_list(self, ip_list):
        def is_ip_forbidden(ip):
            return any(
                [
                    ipaddress.ip_address(ip) in ipaddress.ip_network(net)
                    for net in self.config["forbidden_networks"]
                ]
            )

        if any(map(is_ip_forbidden, ip_list)):
            raise ForbiddenIpError
